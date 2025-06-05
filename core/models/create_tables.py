# core/models/create_tables.py

from core.models.database import Database, Base
from config.secrets import Settings

# Загружаем настройки
settings = Settings()

# Строим DSN по тем же правилам, что и в контейнере:
dsn = (
    f"{settings.DB_TYPE}://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Инициализируем объект Database
db = Database(
    dsn=dsn,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    timeout=settings.DB_TIMEOUT,
    pool_recycle=3600,
    echo=False,  # Можно True для отладки SQL
)

# Создаем все таблицы, объявленные через Base
Base.metadata.create_all(bind=db.engine)
print("All tables created successfully.")
