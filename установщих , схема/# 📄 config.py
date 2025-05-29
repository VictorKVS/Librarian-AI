# 📄 config.py

from pydantic import BaseSettings

class Settings(BaseSettings):
    # Celery и Redis
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    CELERY_LOG_PATH: str = "/var/log/celery.log"
    FLOWER_URL: str = "http://flower:5555"
    
    # Настройки воркеров
    CELERY_WORKERS: int = 4
    CELERY_MAX_TASKS_PER_CHILD: int = 100
    CELERY_TASK_TIME_LIMIT: int = 300