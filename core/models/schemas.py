# core/models/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# --- Документы ---

class DocumentCreate(BaseModel):
    title: str
    content: str


class DocumentResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    chunks: List[str]


# --- Чанки и сущности ---

class EntityResponse(BaseModel):
    text: str
    label: str
    confidence: Optional[float] = None


class ChunkMetadata(BaseModel):
    index: int
    text: str
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None


# --- Основной ответ обработки ---

class ProcessingResponse(BaseModel):
    session_id: str
    processing_time: float
    chunks_processed: int
    entities_found: int
    entities: List[EntityResponse]
    chunks: Optional[List[ChunkMetadata]] = None
    warnings: Optional[List[str]] = []


# --- Асинхронные задачи ---

class AsyncTaskResponse(BaseModel):
    task_id: str
    status_url: str


class AsyncTaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, started, progress, success, failure
    progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    logs: Optional[List[str]] = Field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None


# --- Состояние системы ---

class HealthStatusResponse(BaseModel):
    vector_store: bool
    cache: bool
    embedder: bool
    extractor: bool
    last_checked: str
    version: str


# --- Ошибки ---

class ErrorResponse(BaseModel):
    detail: str


# --- Отладочная трассировка (опционально) ---

class DebugTrace(BaseModel):
    step: str
    timestamp: datetime
    message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
