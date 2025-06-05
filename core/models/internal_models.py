# core/models/internal_models.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Entity:
    """
    Структура для хранения информации об извлечённой сущности.
    :param text: текст сущности
    :param label: тип сущности (например, CVE, THREAT, ROLE и т.д.)
    :param start: позиция начала сущности в исходном тексте
    :param end: позиция конца сущности в исходном тексте
    """
    text: str
    label: str
    start: int
    end: int


@dataclass
class Chunk:
    """
    Структура для хранения одного чанка документа после обработки.
    :param chunk_id: уникальный идентификатор чанка (например, "{doc_id}_chunk_{i}")
    :param text: сам текст чанка
    :param embedding: векторное представление чанка (список float)
    :param entities: список сущностей типа Entity, найденных в этом чанке
    :param metadata: произвольные метаданные, связанные с чанком (например, язык, заголовок документа и т.д.)
    """
    chunk_id: str
    text: str
    embedding: List[float]
    entities: List[Entity]
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Document:
    """
    Итоговая структура обработанного документа.
    :param doc_id: уникальный идентификатор документа
    :param title: опциональный заголовок документа
    :param version: опциональная версия документа
    :param chunks: список объектов Chunk, полученных в результате разбивки и обработки
    """
    doc_id: str
    title: Optional[str] = None
    version: Optional[str] = None
    chunks: List[Chunk] = field(default_factory=list)