# 📄 api/process_router.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from core.document_processor import DocumentProcessor
from core.loader import split_into_chunks
from core.tools.async_tasks import process_document_async, create_status_task
from models.schemas import (
    ProcessingResponse,
    EntityResponse,
    ErrorResponse,
    HealthStatusResponse,
    AsyncTaskResponse
)
from typing import List, Optional
from uuid import uuid4
import aiofiles
import os
import logging
from datetime import datetime
from config import settings
from utils.file_utils import clean_temp_files

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Document Processing"],
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)

# Инициализация процессора
processor = DocumentProcessor(
    max_retries=settings.PROCESSOR_MAX_RETRIES,
    health_check_interval=settings.HEALTH_CHECK_INTERVAL,
    cache_ttl=settings.CACHE_TTL
)

@router.post(
    "/process",
    response_model=ProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process document synchronously"
)
async def process_document(
    file: UploadFile = File(...),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
    chunk_size: int = Query(1000, ge=100, le=5000),
    filters: Optional[List[str]] = Query(None),
    background_tasks: BackgroundTasks = Depends()
):
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        file.file.seek(0)

        start_time = datetime.utcnow()
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail="Unsupported file type")

        temp_path = os.path.join(settings.TEMP_DIR, f"{uuid4()}{file_ext}")
        background_tasks.add_task(clean_temp_files, temp_path)

        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        text = await extract_text(temp_path, file_ext)
        chunks = split_into_chunks(text, chunk_size=chunk_size)
        session_id = str(uuid4())

        embeddings, entities = await processor.process_document(
            chunks,
            source_path=file.filename,
            session_id=session_id,
            extract_params={"min_confidence": min_confidence, "filters": filters}
        )

        return ProcessingResponse(
            session_id=session_id,
            processing_time=(datetime.utcnow() - start_time).total_seconds(),
            chunks_processed=len(embeddings),
            entities_found=len(entities),
            entities=[EntityResponse(**e.to_dict()) for e in entities],
            warnings=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Document processing failed")

@router.post(
    "/async-process",
    response_model=AsyncTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process document asynchronously"
)
async def async_process_document(
    file: UploadFile = File(...),
    min_confidence: float = Query(0.7),
    chunk_size: int = Query(1000),
    filters: Optional[List[str]] = Query(None),
    background_tasks: BackgroundTasks = Depends()
):
    try:
        file_ext = os.path.splitext(file.filename)[1].lower()
        temp_path = os.path.join(settings.TEMP_DIR, f"{uuid4()}{file_ext}")
        background_tasks.add_task(clean_temp_files, temp_path)

        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        task = process_document_async.delay(temp_path)

        return AsyncTaskResponse(
            task_id=task.id,
            status_url=f"/api/v1/tasks/{task.id}"
        )
    except Exception as e:
        logger.error(f"Async processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start async document processing")

@router.get(
    "/health",
    response_model=HealthStatusResponse,
    summary="Service health status"
)
async def health_check():
    try:
        status = await processor.check_health()
        if not all([status.vector_store, status.embedder, status.extractor]):
            raise HTTPException(status_code=503, detail="Service partially unavailable")
        return HealthStatusResponse(
            vector_store=status.vector_store,
            cache=status.cache,
            embedder=status.embedder,
            extractor=status.extractor,
            last_checked=status.last_checked.isoformat(),
            version=settings.VERSION
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

async def extract_text(file_path: str, file_ext: str) -> str:
    try:
        if file_ext == '.txt':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        elif file_ext == '.pdf':
            return await run_in_threadpool(extract_pdf_text, file_path)
        elif file_ext == '.docx':
            return await run_in_threadpool(extract_docx_text, file_path)
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text from {file_ext} file")

def extract_pdf_text(file_path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(file_path)
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise

def extract_docx_text(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"DOCX extraction failed: {str(e)}")
        raise
