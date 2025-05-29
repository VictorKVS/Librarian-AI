# 📄 Файл: fallback_dummy.py
# 📂 Путь: librarian_ai/llm/providers/fallback_dummy.py

import asyncio
import logging
from typing import List, AsyncGenerator
from .base_llm import BaseLLM, ModelInfo, ModelType

logger = logging.getLogger(__name__)

class FallbackDummyProvider(BaseLLM):
    def _initialize_model_info(self) -> ModelInfo:
        return ModelInfo(
            name="DummyLLM",
            provider="fallback",
            model_type=ModelType.CHAT,
            context_length=2048,
            supports_streaming=False,
            supports_embeddings=False,
            version="0.1",
            description="Резервная заглушка для отказоустойчивости"
        )

    async def _async_init(self):
        await asyncio.sleep(0.1)  # Эмуляция инициализации

    async def generate_async(self, prompt: str, **kwargs) -> str:
        logger.warning(f"⚠️ DummyLLM используется вместо настоящей модели для запроса: {prompt[:50]}...")
        return "🔁 [Заглушка ответа от DummyLLM — LLM сейчас недоступен]"

    async def _stream_impl(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        yield await self.generate_async(prompt, **kwargs)

    async def _get_embeddings_impl(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 768 for _ in texts]  # Фиктивные векторы

    async def _check_availability(self) -> bool:
        return True