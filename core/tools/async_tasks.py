# core/tools/async_tasks.py
from celery import Celery

celery_app = Celery(__name__, broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")

@celery_app.task
def process_document_async(doc_id: str):
    # TODO: асинхронная обработка документа (chunking, embedding, summary)
    return {"status": "done", "id": doc_id}