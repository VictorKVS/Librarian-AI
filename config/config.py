# 📄 config/secrets.py
from pydantic import BaseSettings, Field
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    # 📦 PostgreSQL
    DB_TYPE: str = "postgresql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "librarian_db"
    DB_USER: str = "librarian"
    DB_PASSWORD: str = "secretpass"
    DB_REPLICA_HOST: str = ""

    # ⚙️ Пул соединений
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_TIMEOUT: int = 30

    # ⚡ Redis + Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    CELERY_LOG_PATH: str = "/var/log/celery.log"
    FLOWER_URL: str = "http://flower:5555"
    CELERY_WORKERS: int = 4
    CELERY_MAX_TASKS_PER_CHILD: int = 100
    CELERY_TASK_TIME_LIMIT: int = 300

    # 🧠 Qdrant
    QDRANT_HOST: str = "qdrant"

    # 📁 Файлы
    TEMP_DIR: str = "/tmp"
    MAX_FILE_SIZE: int = 10_000_000
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf", ".docx", ".txt"])

    # 🔐 LLM-провайдеры
    LLM_PROVIDER: str = "gigachat"  # По умолчанию GigaChat
    OPENROUTER_KEY: Optional[str] = None
    GIGACHAT_SECRET: Optional[str] = None
    YANDEX_API_KEY: Optional[str] = None
    YANDEX_FOLDER_ID: Optional[str] = None
    MISTRAL_MODEL_PATH: Optional[str] = "mistralai/Mistral-7B-Instruct-v0.2"

    # 🧾 Логирование и версия
    LOG_LEVEL: str = "INFO"
    DB_ECHO: bool = False
    VERSION: str = "2.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()

# 📌 Глобальная переменная для доступа
settings = get_settings()
