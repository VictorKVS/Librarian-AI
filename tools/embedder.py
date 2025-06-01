import asyncio
from functools import lru_cache
from typing import List, Optional, Dict, Union, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingType(Enum):
    """Типы нормализации эмбеддингов"""
    NONE = "none"
    L2 = "l2"
    L1 = "l1"

@dataclass
class CacheInfo:
    """Информация о кэше эмбеддингов"""
    size: int
    usage: int
    hits: int
    misses: int
    hit_rate: float

class Embedder:
    """Продвинутый класс для генерации текстовых эмбеддингов с поддержкой GPU/CPU и кэширования.
    
    Поддерживает как модели из SentenceTransformers, так и стандартные трансформеры из Hugging Face.
    Обеспечивает кэширование, батч-обработку и асинхронный интерфейс.
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        cache_size: int = 2048,
        embedding_type: EmbeddingType = EmbeddingType.L2,
        model_kwargs: Optional[Dict] = None,
        max_seq_length: Optional[int] = None,
    ):
        """
        Args:
            model_name: Название модели в Hugging Face Hub
            device: Устройство для вычислений (None для автоопределения)
            cache_size: Размер кэша эмбеддингов
            embedding_type: Тип нормализации эмбеддингов
            model_kwargs: Дополнительные параметры для модели
            max_seq_length: Максимальная длина последовательности
        """
        self.device = self._resolve_device(device)
        self.embedding_type = embedding_type
        self.model_kwargs = model_kwargs or {}
        self.max_seq_length = max_seq_length
        
        # Инициализация модели
        self._init_model(model_name)
        
        # Настройка кэширования
        self._setup_caching(cache_size)
        
        logger.info(f"Embedder initialized with model {model_name} on {self.device}")
    
    def _resolve_device(self, device: Optional[str]) -> str:
        """Определяет оптимальное устройство для вычислений."""
        if device:
            return device
        return "cuda" if torch.cuda.is_available() else "cpu"
    
    def _init_model(self, model_name: str):
        """Инициализирует модель с обработкой исключений."""
        try:
            self.model = SentenceTransformer(
                model_name,
                device=self.device,
                **self.model_kwargs
            )
            if self.max_seq_length:
                self.model.max_seq_length = self.max_seq_length
            self.use_sentence_transformers = True
            logger.info("Using SentenceTransformer for optimal performance")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}, falling back to AutoModel")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, **self.model_kwargs)
            self.model = AutoModel.from_pretrained(model_name, **self.model_kwargs).to(self.device)
            self.use_sentence_transformers = False
        
        self.model.eval()
    
    def _setup_caching(self, cache_size: int):
        """Настраивает систему кэширования."""
        self._encode_sync = lru_cache(maxsize=cache_size)(self._encode_sync_uncached)
        self.cache_enabled = cache_size > 0
        
    def _normalize_embeddings(self, embeddings: torch.Tensor) -> torch.Tensor:
        """Применяет нормализацию к эмбеддингам."""
        if self.embedding_type == EmbeddingType.L2:
            return torch.nn.functional.normalize(embeddings, p=2, dim=1)
        elif self.embedding_type == EmbeddingType.L1:
            return torch.nn.functional.normalize(embeddings, p=1, dim=1)
        return embeddings
    
    def _encode_sync_uncached(self, text: str) -> List[float]:
        """Синхронная генерация эмбеддинга без кэширования."""
        try:
            if self.use_sentence_transformers:
                embedding = self.model.encode(
                    text,
                    convert_to_tensor=True,
                    show_progress_bar=False,
                    normalize_embeddings=False  # Нормализуем сами для гибкости
                )
            else:
                inputs = self.tokenizer(
                    text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=self.max_seq_length or 512,
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    embedding = self._mean_pooling(outputs, inputs['attention_mask'])
            
            embedding = self._normalize_embeddings(embedding)
            return embedding.cpu().tolist()
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise
    
    def _mean_pooling(self, model_output, attention_mask) -> torch.Tensor:
        """Mean pooling для получения эмбеддинга из токенов."""
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = (
            attention_mask
            .unsqueeze(-1)
            .expand(token_embeddings.size())
            .float()
        )
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
    
    async def generate(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> Union[List[float], List[List[float]]]:
        """
        Асинхронная генерация эмбеддингов
        
        Args:
            texts: Текст или список текстов
            batch_size: Размер батча (для списков)
            show_progress: Показывать прогресс-бар
            
        Returns:
            Эмбеддинг или список эмбеддингов
        """
        if isinstance(texts, str):
            return await self._generate_single(texts)
        return await self._generate_batch(texts, batch_size, show_progress)
    
    async def _generate_single(self, text: str) -> List[float]:
        """Генерация эмбеддинга для одного текста."""
        if not self.cache_enabled:
            return await self._run_in_executor(self._encode_sync_uncached, text)
        return self._encode_sync(text)
    
    async def _generate_batch(
        self,
        texts: List[str],
        batch_size: int,
        show_progress: bool
    ) -> List[List[float]]:
        """Генерация эмбеддингов для списка текстов."""
        if self.use_sentence_transformers:
            return await self._generate_batch_st(texts, batch_size, show_progress)
        return await self._generate_batch_hf(texts, batch_size)
    
    async def _generate_batch_st(
        self,
        texts: List[str],
        batch_size: int,
        show_progress: bool
    ) -> List[List[float]]:
        """Генерация батча с использованием SentenceTransformers."""
        embeddings = await self._run_in_executor(
            self.model.encode,
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=False
        )
        embeddings = torch.from_numpy(embeddings).to(self.device)
        embeddings = self._normalize_embeddings(embeddings)
        return embeddings.cpu().tolist()
    
    async def _generate_batch_hf(
        self,
        texts: List[str],
        batch_size: int
    ) -> List[List[float]]:
        """Генерация батча с использованием AutoModel."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._run_in_executor(
                self._encode_batch_hf,
                batch
            )
            embeddings.extend(batch_embeddings)
        return embeddings
    
    def _encode_batch_hf(self, texts: List[str]) -> List[List[float]]:
        """Синхронная обработка батча текстов с помощью AutoModel."""
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_seq_length or 512,
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
            embeddings = self._normalize_embeddings(embeddings)
            return embeddings.cpu().tolist()
    
    async def _run_in_executor(self, func, *args):
        """Запускает синхронную функцию в executor'е."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
    
    def clear_cache(self) -> None:
        """Очищает кэш эмбеддингов."""
        if hasattr(self, '_encode_sync'):
            self._encode_sync.cache_clear()
            logger.info("Embedding cache cleared")
    
    def get_cache_info(self) -> CacheInfo:
        """Возвращает подробную информацию о кэше."""
        if not hasattr(self, '_encode_sync'):
            return CacheInfo(0, 0, 0, 0, 0.0)
        
        info = self._encode_sync.cache_info()
        hit_rate = info.hits / max(1, info.hits + info.misses)
        return CacheInfo(
            size=info.maxsize,
            usage=info.currsize,
            hits=info.hits,
            misses=info.misses,
            hit_rate=hit_rate
        )
    
    def get_model_info(self) -> Dict:
        """Возвращает информацию о модели."""
        return {
            "model_type": "SentenceTransformer" if self.use_sentence_transformers else "AutoModel",
            "device": self.device,
            "embedding_type": self.embedding_type.value,
            "max_seq_length": getattr(self.model, 'max_seq_length', None)
        }

# Пример использования
async def example_usage():
    # Инициализация эмбеддера с мультиязычной моделью
    embedder = Embedder(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    # Список текстов для обработки
    texts = [
        "Пример текста на русском языке",
        "Another text in English",
        "Un autre texte en français",
        # Добавьте больше текстов по мере необходимости
    ]
    
    # Генерация эмбеддингов с использованием батчей
    embeddings = await embedder.generate_batch(texts, batch_size=64, show_progress=True)
    
    # Вывод результатов
    print(f"Generated {len(embeddings)} embeddings")
    print("First embedding:", embeddings[0][:10])  # Вывод первых 10 значений первого эмбеддинга

# Запуск асинхронной функции
asyncio.run(example_usage())