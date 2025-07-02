# 📄 I:\Librarian-AI\config\secrets.py

# 📄 config/secrets.py

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    # 📦 PostgreSQL (основная БД)
    DB_TYPE: str = "postgresql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "librarian_db"
    DB_USER: str = "librarian"
    DB_PASSWORD: str = "secretpass"
    DB_REPLICA_HOST: Optional[str] = ""

    # ⚙️ Пул соединений PostgreSQL
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # ⚡ Redis + Celery (асинхронные задачи)
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    CELERY_LOG_PATH: str = "/var/log/celery.log"
    FLOWER_URL: str = "http://flower:5555"
    CELERY_WORKERS: int = 4
    CELERY_MAX_TASKS_PER_CHILD: int = 100
    CELERY_TASK_TIME_LIMIT: int = 300

    # 🧠 Qdrant (векторное хранилище)
    QDRANT_HOST: str = "qdrant"

    # 📁 Работа с файлами
    TEMP_DIR: str = "/tmp"
    MAX_FILE_SIZE: int = 10_000_000
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf", ".docx", ".txt"])

    # 🧾 Логирование и версия
    LOG_LEVEL: str = "INFO"
    VERSION: str = "2.0.0"

    # 🆓 Выбор AI-провайдера
    AI_PROVIDER: str = "gigachat"  # варианты: deepseek, gigachat, ollama, huggingface, openrouter, local

    # 🔐 GigaChat (Сбер)
    GIGACHAT_API_OAUTH_URL: Optional[str] = None
    GIGACHAT_API_URL:       Optional[str] = None
    GIGACHAT_API_KEY:       Optional[str] = Field(None, env="GIGACHAT_SECRET")

    # 🆓 DeepSeek Chat
    DEEPSEEK_API_URL: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    # 🤗 HuggingFace Inference API
    HF_API_URL: Optional[str] = None
    HF_TOKEN:   Optional[str] = None

    # 🦜🔗 OpenRouter
    OPENROUTER_URL:     Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = Field(None, env="OPENROUTER_KEY")

    # ☁️ Yandex Cloud LLM
    YANDEX_API_KEY:    Optional[str] = None
    YANDEX_FOLDER_ID:  Optional[str] = None

    # 🧠 Mistral Local
    MISTRAL_MODEL_PATH: Optional[str] = "mistralai/Mistral-7B-Instruct-v0.2"

    # 🔌 Локальный AI-сервер (Ollama / Llama.cpp)
    LOCAL_AI_URL:   Optional[str] = "http://localhost:11434"
    LOCAL_AI_MODEL: Optional[str] = "llama3"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# 📌 Глобальный объект с настройками
settings = get_settings()
