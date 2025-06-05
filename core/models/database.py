# core/models/database.py

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session, scoped_session

# Базовый класс для объявлений ORM-моделей (если в будущем понадобятся)
Base = declarative_base()

class Database:
    """
    Обёртка для SQLAlchemy Engine и SessionLocal с улучшенной управляемостью:
    - pool_recycle для «мертвых» соединений,
    - echo для отладки SQL,
    - @contextmanager для автоматического коммита/роллбека.
    """

    def __init__(
        self,
        dsn: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        """
        :param dsn: строка подключения (например, "postgresql://user:pass@host:port/dbname")
        :param pool_size: размер основного пула соединений
        :param max_overflow: число «запасных» соединений сверх pool_size
        :param timeout: таймаут подключения (в секундах)
        :param pool_recycle: пересоздавать соединения каждые N секунд (избегаем «мертвых» подключений)
        :param echo: логировать SQL-запросы (True для отладки)
        """
        self.engine = create_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            connect_args={"connect_timeout": timeout},
            pool_recycle=pool_recycle,
            echo=echo,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        # Если понадобится thread-local сессия:
        # self.SessionLocal = scoped_session(self.SessionLocal)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Контекстный менеджер для Dependency Injection в FastAPI.
        При успехе автоматически коммитит, при ошибке — откатывает.
        Пример использования:
            @app.get("/items")
            def read_items(db: Session = Depends(db_provider.get_session)):
                ...
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_sync_session(self) -> Session:
        """
        Для случаев, когда нужен «ручной» синхронный доступ к БД вне контекста FastAPI:
            with db.get_sync_session() as session:
                ...
        """
        return self.SessionLocal()
