# 📄 tasks/document_processor.py

from celery import Celery
from core.document_processor import DocumentProcessor
from config import settings
import logging
from celery.signals import after_setup_logger

logger = logging.getLogger(__name__)

# Инициализация Celery
celery_app = Celery(
    "document_processor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True
)

# Конфигурация Celery
celery_app.conf.update({
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_track_started': True,
    'worker_prefetch_multiplier': 1,
    'broker_transport_options': {
        'visibility_timeout': 3600,
        'fanout_prefix': True
    }
})

@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """Настройка логгирования для Celery"""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(settings.CELERY_LOG_PATH)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@celery_app.task(
    bind=True,
    name="process_document",
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_backoff_max=60,
    retry_kwargs={'max_retries': 3},
    time_limit=300,
    soft_time_limit=240
)
def process_document_task(self, file_data: dict):
    """Главная задача обработки документа"""
    try:
        processor = DocumentProcessor()
        
        # Обработка файла
        result = processor.process_document(
            chunks=file_data['chunks'],
            source_path=file_data['source_path'],
            session_id=file_data['session_id'],
            extract_params=file_data['extract_params']
        )
        
        return {
            'status': 'SUCCESS',
            'result': {
                'embeddings': [emb.tolist() for emb, _ in result[0]],
                'entities': [ent.to_dict() for ent in result[1]]
            }
        }
    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e)

