# 📄 Файл: storage.py
# 📂 Путь: db/
# 📌 Назначение: Инициализация базы данных PostgreSQL с pgvector, поддержкой реплики, пулами соединений, метриками и безопасным доступом к сессиям

import os
import time
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.event import listens_for

from prometheus_client import Gauge, Histogram

from db.models import Base

# 🔧 Настройка логгера
logger = logging.getLogger("db.storage")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

# 📊 Метрики для мониторинга
DB_CONNECTIONS = Gauge("db_connections", "Active database connections")
DB_QUERY_TIME = Histogram("db_query_time", "DB query time (seconds)")

# ⚙️ Конфигурация подключения
class DatabaseConfig:
    def __init__(self):
        self.db_type = os.getenv("DB_TYPE", "postgresql")
        self.user = os.getenv("DB_USER", "librarian")
        self.password = os.getenv("DB_PASSWORD", "secretpass")
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.name = os.getenv("DB_NAME", "librarian_db")
        self.replica_host = os.getenv("DB_REPLICA_HOST")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", 20))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 10))
        self.timeout = int(os.getenv("DB_TIMEOUT", 30))

    def get_master_url(self):
        if self.db_type == "postgresql":
            return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return "sqlite:///storage/librarian.db"

    def get_replica_url(self):
        if self.replica_host:
            return f"postgresql+psycopg2://{self.user}:{self.password}@{self.replica_host}:{self.port}/{self.name}"
        return None

# 🧠 Конфигурация БД
db_config = DatabaseConfig()

# 🚀 Создание движков
def create_engine_with_config(url, **kwargs):
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_pre_ping=True,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_timeout=db_config.timeout,
        connect_args={"connect_timeout": db_config.timeout},
        **kwargs
    )

engine = create_engine_with_config(
    db_config.get_master_url(),
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

replica_engine = None
if db_config.get_replica_url():
    replica_engine = create_engine_with_config(db_config.get_replica_url(), echo=False)

# 🔁 Сессии
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
ReplicaSessionLocal = sessionmaker(bind=replica_engine if replica_engine else engine, autocommit=False, autoflush=False, expire_on_commit=False)
ScopedSession = scoped_session(SessionLocal)

# 📦 Контекстный менеджер
@contextmanager
def session_scope(replica=False):
    """Контекст для безопасной работы с сессией БД"""
    session = ReplicaSessionLocal() if replica and replica_engine else SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"[DB] Ошибка транзакции: {e}")
        raise
    finally:
        session.close()

# 🏗️ Инициализация БД
def init_db():
    """Создание таблиц и установка расширений"""
    try:
        with engine.connect() as conn:
            if engine.url.drivername.startswith("postgresql"):
                extensions = ["vector", "pg_trgm", "hstore", "pg_stat_statements"]
                for ext in extensions:
                    try:
                        conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
                        logger.info(f"[DB] Расширение {ext} — готово.")
                    except exc.ProgrammingError as e:
                        logger.warning(f"[DB] Не удалось установить {ext}: {e}")
            conn.execute(text("SET statement_timeout = '30s'"))
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы и расширения базы данных успешно созданы.")
    except exc.OperationalError as e:
        logger.critical(f"❌ Ошибка подключения к базе данных: {e}")
        raise

# 📈 Метрики Prometheus (опционально)
@listens_for(engine, "connect")
def track_connections(dbapi_connection, connection_record):
    DB_CONNECTIONS.inc()

@listens_for(engine, "close")
def track_disconnections(dbapi_connection, connection_record):
    DB_CONNECTIONS.dec()

@listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - context._query_start_time
    DB_QUERY_TIME.observe(duration)
