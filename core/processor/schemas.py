# core/processor/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="UUID чанка")
    text: str = Field(..., description="Текст чанка")
    embedding: List[float] = Field(..., description="Вектор эмбеддинга")
    entities: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Список сущностей, найденных в чанке"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Метаданные чанка (например, ссылку на документ)"
    )

class ProcessedDocument(BaseModel):
    """
    Итог работы DocumentProcessor: 
    doc_id, список обработанных чанков, опц. заголовок и версия.
    """
    doc_id: str = Field(..., description="UUID документа")
    chunks: List[DocumentChunk] = Field(..., description="Список чанков")
    title: Optional[str] = Field(None, description="Заголовок документа")
    version: Optional[str] = Field(None, description="Версия документа")

class RetrieverResult(BaseModel):
    """
    Расширенная схема результата поиска:
    chunk_id, текст, скор и список сущностей.
    """
    chunk_id: str = Field(..., description="UUID найденного чанка")
    text: str = Field(..., description="Текст чанка")
    score: float = Field(..., description="Косинусное сходство / скор")
    entities: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Сущности, найденные в тексте чанка"
    )