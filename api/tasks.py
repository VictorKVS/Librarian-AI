# 📄 api/tasks.py

from fastapi import APIRouter, HTTPException
from core.tools.async_tasks import get_task_status, cancel_task
from core.models.schemas import AsyncTaskStatusResponse, ErrorResponse

router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["Task Management"],
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

@router.get(
    "/{task_id}",
    response_model=AsyncTaskStatusResponse,
    summary="Get status of asynchronous task",
    description="Returns current status, progress, logs and result of a background processing task"
)
def get_task_status_route(task_id: str):
    try:
        task_info = get_task_status(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")
        return AsyncTaskStatusResponse(**task_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")

@router.post(
    "/{task_id}/cancel",
    response_model=dict,
    summary="Cancel asynchronous task",
    description="Forcefully cancels a running background processing task"
)
def cancel_task_route(task_id: str):
    try:
        return cancel_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")
