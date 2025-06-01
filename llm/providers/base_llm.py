# 📄 Файл: base_llm.py
# 📂 Путь: librarian_ai/llm/providers/base_llm.py

"""Поддержка типов моделей (ModelType)

ModelInfo включает timeout, batch_size, rate_limit, max_retries

Контекстный менеджер (async with)

Асинхронная и потоковая генерация (stream)

Автоматическая нормализация эмбеддингов

Грейсфул деградация при ошибках

🧠 Готово к использованию с SmartRouter, QualityAnalyzer, MemoryAugmenter, провайдерами (yandex_gpt.py, deepseek.py, и д"""





from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum, auto
import logging
import asyncio
from contextlib import asynccontextmanager
import numpy as np

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Типы поддерживаемых моделей"""
    CHAT = auto()
    INSTRUCT = auto()
    EMBEDDING = auto()
    MULTIMODAL = auto()
    CODE = auto()

@dataclass(frozen=True)
class ModelInfo:
    """Неизменяемые метаданные модели"""
    name: str
    provider: str
    model_type: ModelType = ModelType.CHAT
    context_length: int = 8192
    supports_streaming: bool = False
    supports_embeddings: bool = False
    supports_vision: bool = False
    version: str = "1.0"
    description: Optional[str] = None
    cost_per_token: Optional[float] = None
    max_retries: int = 3
    timeout: float = 30.0
    batch_size: Optional[int] = None
    rate_limit_qps: Optional[int] = None
    concurrency_limit: Optional[int] = None

class BaseLLM(ABC):
    """
    Базовый класс для всех LLM-провайдеров
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._model_info = self._initialize_model_info()
        self._initialized = False
        self._session = None

    @property
    def model_info(self) -> ModelInfo:
        return self._model_info

    @abstractmethod
    def _initialize_model_info(self) -> ModelInfo:
        """Создаёт объект ModelInfo"""
        raise NotImplementedError

    async def initialize(self) -> None:
        if not self._initialized:
            try:
                await self._async_init()
                self._initialized = True
                logger.info(f"[{self}] инициализирован")
            except Exception as e:
                logger.exception(f"Ошибка инициализации {self}: {e}")
                raise

    @abstractmethod
    async def _async_init(self) -> None:
        pass

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        pass

    async def stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        try:
            if self.model_info.supports_streaming:
                async for chunk in self._stream_impl(prompt, **kwargs):
                    yield chunk
            else:
                response = await self.generate_async(prompt, **kwargs)
                yield response
        except Exception as e:
            logger.exception(f"[{self}] Ошибка при stream: {e}")
            yield f"[Ошибка] {str(e)}"

    @abstractmethod
    async def _stream_impl(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            return asyncio.run(self.generate_async(prompt, **kwargs))
        except Exception as e:
            logger.error(f"[{self}] Синхронная генерация не удалась: {str(e)}")
            return f"[Ошибка] {str(e)}"

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.model_info.supports_embeddings:
            raise NotImplementedError("Эта модель не поддерживает эмбеддинги")
        vectors = await self._get_embeddings_impl(texts)
        return self._normalize_embeddings(vectors)

    @abstractmethod
    async def _get_embeddings_impl(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def _normalize_embeddings(self, vectors: List[List[float]]) -> List[List[float]]:
        try:
            array = np.array(vectors)
            norm = np.linalg.norm(array, axis=1, keepdims=True)
            norm[norm == 0] = 1e-8
            normalized = array / norm
            return normalized.tolist()
        except Exception as e:
            logger.warning(f"Не удалось нормализовать эмбеддинги: {str(e)}")
            return vectors

    async def is_available(self) -> bool:
        for attempt in range(self.model_info.max_retries):
            try:
                return await self._check_availability()
            except Exception as e:
                logger.warning(f"[{self}] Попытка #{attempt+1} не удалась: {e}")
                await asyncio.sleep(1)
        return False

    async def _check_availability(self) -> bool:
        return True

    async def close(self) -> None:
        if self._initialized:
            try:
                await self._async_close()
                self._initialized = False
                logger.info(f"[{self}] корректно закрыт")
            except Exception as e:
                logger.error(f"[{self}] ошибка закрытия: {e}")

    async def _async_close(self) -> None:
        pass

    @asynccontextmanager
    async def context(self):
        await self.initialize()
        try:
            yield self
        finally:
            await self.close()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __str__(self) -> str:
        return f"{self.model_info.provider}:{self.model_info.name}"

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} "
                f"provider={self.model_info.provider} "
                f"name={self.model_info.name} "
                f"type={self.model_info.model_type.name} "
                f"v{self.model_info.version}>")
