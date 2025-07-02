#core/parser/chunker.py
from typing import List, Optional, Dict
import re
import html
from enum import Enum, auto
import logging
from collections import Counter
from functools import lru_cache
from dataclasses import dataclass
import unicodedata
from transformers import pipeline
import torch
import concurrent.futures

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChunkingStrategy(Enum):
    """Стратегии разбиения текста на чанки"""
    SENTENCE = auto()
    PARAGRAPH = auto()
    MIXED = auto()
    SMART = auto()
    LEARNED = auto()  # Новая стратегия, использующая обучение

@dataclass
class ChunkStats:
    total_chunks: int
    avg_size: float
    size_distribution: Dict[str, int]
    sentences_dist: Dict[int, int]
    language: str
    readability_score: Optional[float] = None

class TextChunker:
    """Умное разбиение текста с поддержкой ML-обучения и расширенной функциональностью"""
    
    def __init__(
        self,
        max_length: int = 1000,
        translation_model: Optional[str] = None,
        spacy_model: Optional[str] = None,
        ml_model: Optional[str] = None,
        parallel_workers: int = 4
    ):
        self.max_length = max_length
        self.translator = self._load_translator(translation_model)
        self.nlp = self._load_spacy_model(spacy_model)
        self._init_patterns()
        self.learning_model = self._load_learning_model(ml_model)
        self.parallel_workers = parallel_workers

    def _load_learning_model(self, model_name: Optional[str]):
        """Загрузка обучающей модели"""
        if model_name:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                return pipeline("text-generation", model=model_name, device=device)
            except Exception as e:
                logger.warning(f"Failed to load learning model: {e}")
        return None

    async def chunk(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        language: Optional[str] = None,
        strategy: ChunkingStrategy = ChunkingStrategy.LEARNED,
        preserve_formatting: bool = False,
        merge_strategy: str = 'aggressive',
        min_chunk_size: int = 100,
        remove_stopwords: bool = False,
        target_language: Optional[str] = None
    ) -> List[str]:
        """Динамическое разбиение текста с возможностью обучения и параллельного исполнения"""
        text = self._preprocess_text(text, preserve_formatting)
        if not text.strip():
            return []
        language = language or self.detect_language(text)
        if strategy == ChunkingStrategy.LEARNED and self.learning_model:
            chunks = await self._learned_chunking(text, chunk_size or self.max_length, language)
        else:
            chunks = self._apply_chunking_strategy(text, chunk_size or self.max_length, language, strategy)
        chunks = self._postprocess_chunks(chunks, chunk_size or self.max_length, merge_strategy, min_chunk_size)
        if target_language and self.translator:
            chunks = await self._translate_chunks(chunks, language, target_language)
        return chunks

    def _preprocess_text(self, text: str, preserve_formatting: bool) -> str:
        """Предварительная обработка текста."""
        text = unicodedata.normalize('NFKC', text)
        if not preserve_formatting:
            text = re.sub(r'\s+', ' ', text).strip()
        return html.unescape(text)

    def _calculate_avg_sentence_len(self, text: str, language: str) -> float:
        """Вычисляет среднюю длину предложения."""
        pattern = self._sentence_patterns.get(language, self._sentence_patterns['default'])
        sentences = [s for s in re.split(pattern, text) if s.strip()]
        return sum(len(s) for s in sentences)/len(sentences) if sentences else 0

    def _apply_chunking_strategy(self, text: str, chunk_size: int, language: str, strategy: ChunkingStrategy) -> List[str]:
        if strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentences(text, chunk_size, language)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraphs(text, chunk_size)
        elif strategy == ChunkingStrategy.MIXED:
            return self._mixed_chunking(text, chunk_size, language)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

    def _chunk_by_sentences(self, text: str, chunk_size: int, language: str) -> List[str]:
        pattern = self._sentence_patterns.get(language, self._sentence_patterns['default'])
        sentences = [s for s in re.split(pattern, text) if s.strip()]
        chunks, current_chunk, current_length = [], [], 0
        for sentence in sentences:
            sent_len = len(sentence)
            if current_length + sent_len <= chunk_size:
                current_chunk.append(sentence)
                current_length += sent_len + 1
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                if sent_len > chunk_size:
                    forced = self._force_chunk(sentence, chunk_size)
                    chunks.extend(forced[:-1])
                    current_chunk = [forced[-1]]
                    current_length = len(forced[-1])
                else:
                    current_chunk = [sentence]
                    current_length = sent_len
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        return chunks

    def _chunk_by_paragraphs(self, text: str, chunk_size: int) -> List[str]:
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        chunks, current_chunk, current_length = [], [], 0
        for para in paragraphs:
            para_len = len(para)
            if current_length + para_len <= chunk_size:
                current_chunk.append(para)
                current_length += para_len + 1
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                if para_len > chunk_size:
                    forced = self._force_chunk(para, chunk_size)
                    chunks.extend(forced[:-1])
                    current_chunk = [forced[-1]]
                    current_length = len(forced[-1])
                else:
                    current_chunk = [para]
                    current_length = para_len
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        return chunks

    def _force_chunk(self, text: str, chunk_size: int) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def _mixed_chunking(self, text: str, chunk_size: int, language: str) -> List[str]:
        paragraphs = text.split('\n\n')
        chunks = []
        for para in paragraphs:
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                chunks.extend(self._chunk_by_sentences(para, chunk_size, language))
        return chunks

    def _postprocess_chunks(self, chunks: List[str], chunk_size: int, merge_strategy: str, min_chunk_size: int) -> List[str]:
        if merge_strategy == 'aggressive':
            return self._merge_chunks_aggressive(chunks, chunk_size, min_chunk_size)
        return self._merge_chunks_conservative(chunks, chunk_size, min_chunk_size)

    def _merge_chunks_aggressive(self, chunks: List[str], max_size: int, min_size: int) -> List[str]:
        merged, current = [], ""
        for chunk in chunks:
            if len(current) + len(chunk) <= max_size:
                current = f"{current} {chunk}".strip()
            else:
                if current:
                    merged.append(current)
                current = chunk if len(chunk) >= min_size else ""
        if current:
            merged.append(current)
        return merged

    def _merge_chunks_conservative(self, chunks: List[str], max_size: int, min_size: int) -> List[str]:
        merged = []
        for chunk in chunks:
            if not merged:
                merged.append(chunk)
            elif len(merged[-1]) + len(chunk) <= max_size and len(merged[-1]) < min_size:
                merged[-1] = f"{merged[-1]} {chunk}"
            else:
                merged.append(chunk)
        return merged

    def _calculate_stats(self, chunks: List[str]) -> ChunkStats:
        sizes = [len(c) for c in chunks]
        sentences = [c.count('.') + c.count('!') + c.count('?') for c in chunks]
        return ChunkStats(
            total_chunks=len(chunks),
            avg_size=sum(sizes)/len(sizes) if chunks else 0,
            size_distribution=Counter(
                "tiny" if s < 100 else
                "small" if s < 300 else
                "medium" if s < 700 else
                "large" for s in sizes
            ),
            sentences_dist=Counter(sentences)
        )