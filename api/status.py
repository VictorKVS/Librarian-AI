# 📄 Файл: api/status.py
from fastapi import APIRouter, Response, status
from celery.result import AsyncResult
from core.tools.async_tasks import celery
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float = None
    result: object = None
    error: str = None

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    try:
        task = AsyncResult(task_id, app=celery)
        
        # Если задача еще не началась
        if task.state == 'PENDING':
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state
            )
        
        # Если задача в процессе выполнения
        elif task.state == 'STARTED' or task.state == 'PROGRESS':
            info = task.info or {}
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state,
                progress=float(info.get('progress', 0)),
                result=None
            )
        
        # Если задача успешно завершена
        elif task.successful():
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state,
                result=task.result
            )
        
        # Если задача провалилась
        elif task.failed():
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state,
                error=str(task.result)
            )
        
        # Любой другой статус
        else:
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state
            )
    
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal Server Error: {str(e)}"}
        )