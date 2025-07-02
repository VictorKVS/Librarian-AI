# core/tools/async_tasks.py

from celery import Celery
from celery.result import AsyncResult
import logging
from typing import Dict, Any
from datetime import datetime

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройка Celery с использованием Redis
celery_app = Celery(
    __name__,
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)

class DocumentProcessingError(Exception):
    """Кастомное исключение для ошибок обработки документов"""
    pass

@celery_app.task(bind=True, name="document_processing")
def process_document_async(self, doc_id: str) -> Dict[str, Any]:
    """
    Асинхронная задача: обработка документа по ID (или пути).
    """

    logs = []
    started_at = datetime.utcnow().isoformat()

    try:
        def log(stage: str, progress: float):
            logs.append(stage)
            self.update_state(state='PROGRESS', meta={
                "stage": stage,
                "progress": progress,
                "logs": logs,
                "started_at": started_at
            })
            logger.info(f"[{doc_id}] {stage}")

        # Пайплайн
        log("📁 Загрузка документа", 0.1)
        # document = DocumentLoader.load(doc_id)

        log("🧹 Предобработка текста", 0.2)
        # processed_text = TextPreprocessor.process(document)

        log("✂️ Чанкование текста", 0.4)
        # chunks = TextChunker.chunk(processed_text)

        log("📊 Генерация эмбеддингов", 0.6)
        # embeddings = EmbeddingGenerator.generate(chunks)

        log("🧠 Аннотирование", 0.8)
        # annotations = AnnotationGenerator.annotate(embeddings)

        log("💾 Сохранение результатов", 0.95)
        # StorageService.save_results(doc_id, embeddings, annotations)

        finished_at = datetime.utcnow().isoformat()

        return {
            "status": "done",
            "doc_id": doc_id,
            "progress": 1.0,
            "started_at": started_at,
            "finished_at": finished_at,
            "logs": logs
        }

    except Exception as e:
        error_msg = f"[{doc_id}] ❌ Ошибка обработки: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logs.append(error_msg)
        self.update_state(state='FAILURE', meta={
            "error": error_msg,
            "progress": 0.0,
            "logs": logs,
            "started_at": started_at
        })
        raise DocumentProcessingError(error_msg) from e


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Получает статус Celery-задачи по task_id.
    """
    result = AsyncResult(task_id, app=celery_app)

    status = {
        "task_id": task_id,
        "status": result.status,
        "result": result.result
    }

    if result.status == 'PROGRESS':
        status.update(result.info or {})
    elif result.status == 'FAILURE':
        status["error"] = str(result.info)

    return status


def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Принудительно отменяет задачу по её ID.
    """
    try:
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        logger.warning(f"Задача {task_id} отменена вручную")
        return {
            "task_id": task_id,
            "success": True,
            "message": "Задача отменена"
        }
    except Exception as e:
        logger.error(f"Ошибка отмены задачи {task_id}: {str(e)}")
        return {
            "task_id": task_id,
            "success": False,
            "message": f"Ошибка отмены: {str(e)}"
        }
