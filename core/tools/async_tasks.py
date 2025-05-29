# 📄 Файл: core/tools/async_tasks.py
# 📌 Назначение: Асинхронные задачи Celery для обработки файлов с поддержкой прогресса и повторных попыток

import asyncio
from pathlib import Path
from typing import Union, Dict, Optional
from celery import Celery
from celery.exceptions import Reject
from core.parser.chunker import TextChunker
from core.tools.loader import FileLoader
from models import ProcessingResult
import logging

logger = logging.getLogger(__name__)

# 🔗 Настройка Celery с Redis
celery = Celery(
    "librarian",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    task_track_started=True,
    result_extended=True
)

# Конфигурация задач
celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,  # 5 минут на задачу
    task_soft_time_limit=240  # Предупреждение через 4 минуты
)

class FileProcessor:
    """Синхронный интерфейс для обработки файлов"""
    
    def __init__(self):
        self.chunker = TextChunker()
        self.loader = FileLoader(self.chunker)
    
    def load_file_sync(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 1000,
        max_chunks: Optional[int] = None,
        language: str = "auto"
    ) -> ProcessingResult:
        """
        Синхронная обработка файла
        Args:
            file_path: Путь к файлу
            chunk_size: Размер чанков в символах
            max_chunks: Максимальное количество чанков
            language: Язык текста (auto для автоопределения)
        Returns:
            ProcessingResult с чанками и метаданными
        """
        try:
            return asyncio.run(
                self.loader.load_file(
                    str(file_path),
                    chunk_size=chunk_size,
                    max_chunks=max_chunks,
                    language=language
                )
            )
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            raise

# Инициализация синхронного процессора
processor = FileProcessor()

@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_kwargs={'max_retries': 3},
    rate_limit='10/m'  # Ограничение: 10 задач в минуту
)
def process_file_task(self, file_path: str, user_id: Optional[str] = None) -> Dict:
    """
    Фоновая задача обработки файла с отслеживанием прогресса
    Args:
        file_path: Абсолютный путь к файлу
        user_id: Идентификатор пользователя для отслеживания
    Returns:
        Словарь с результатами обработки
    """
    try:
        # Обновление статуса задачи
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Analyzing file', 'progress': 10}
        )
        
        # Основная обработка
        result = processor.load_file_sync(file_path)
        
        # Дополнительные метрики
        metrics = {
            'filename': Path(file_path).name,
            'file_size': result.metadata.size,
            'chunk_count': len(result.chunks),
            'language': result.metadata.language,
            'processing_time': round(result.processing_time, 2),
            'user_id': user_id
        }
        
        # Логирование успеха
        logger.info(f"Successfully processed {file_path}")
        return metrics
        
    except Exception as e:
        logger.error(f"Task failed for {file_path}: {str(e)}")
        # Отправка задачи в очередь мертвых писем после 3 попыток
        if self.request.retries == self.max_retries:
            self.send_event(
                'task-failed',
                exception=str(e),
                filename=file_path
            )
        raise Reject(str(e), requeue=False)

@celery.task
def cleanup_temp_files(file_paths: List[str]):
    """Фоновая задача для очистки временных файлов"""
    for path in file_paths:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete {path}: {str(e)}")

def create_chain(file_paths: List[str], user_id: str) -> Dict:
    """
    Создает цепочку задач для обработки нескольких файлов
    Returns:
        Словарь с ID корневой задачи и количеством файлов
    """
    chain = (
        process_file_task.s(file_path, user_id)
        for file_path in file_paths
    )
    result = celery.chain(chain).apply_async()
    return {
        'task_id': result.parent.id,
        'file_count': len(file_paths)
    }