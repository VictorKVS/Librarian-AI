# 📄 Файл: db/storage.py

import os
import time
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional

from sqlalchemy import create_engine, text, exc, Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base, relationship
from sqlalchemy.pool import QueuePool
from sqlalchemy.event import listens_for
from prometheus_client import Gauge, Histogram

from datetime import datetime

# 🔧 Настройка логгера
logger = logging.getLogger("db.storage")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

# 📊 Метрики
DB_CONNECTIONS = Gauge("db_connections", "Active database connections")
DB_QUERY_TIME = Histogram("db_query_time", "DB query time (seconds)")

# 🧱 ORM База
Base = declarative_base()

# ⚙️ Конфигурация
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

# 📦 Конфигурация БД
db_config = DatabaseConfig()

# 🚀 Движки
engine = create_engine(
    db_config.get_master_url(),
    poolclass=QueuePool,
    pool_pre_ping=True,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_timeout=db_config.timeout,
    connect_args={"connect_timeout": db_config.timeout},
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

replica_engine = None
if db_config.get_replica_url():
    replica_engine = create_engine(db_config.get_replica_url(), echo=False)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
ReplicaSessionLocal = sessionmaker(bind=replica_engine or engine, autocommit=False, autoflush=False, expire_on_commit=False)
ScopedSession = scoped_session(SessionLocal)

@contextmanager
def session_scope(replica=False):
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

# 🧠 Модели
class SessionModel(Base):
    __tablename__ = 'sessions'
    session_id = Column(String, primary_key=True)
    user_id = Column(String)
    original_filename = Column(String)
    processing_status = Column(String)
    session_data = Column(JSON)
    vector_path = Column(String)
    graph_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entities = relationship("SessionEntity", back_populates="session")

class EntityModel(Base):
    __tablename__ = 'entities'
    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    normalized_value = Column(Text)
    entity_type = Column(String)
    language = Column(String)
    confidence = Column(Float, default=1.0)
    context = Column(Text)
    source = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("SessionEntity", back_populates="entity")

class SessionEntity(Base):
    __tablename__ = 'session_entities'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.session_id'))
    entity_id = Column(Integer, ForeignKey('entities.id'))

    session = relationship("SessionModel", back_populates="entities")
    entity = relationship("EntityModel", back_populates="sessions")

# 🏗️ Инициализация

def init_db():
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

# 📈 Метрики
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
