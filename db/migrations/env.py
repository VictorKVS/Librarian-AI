# 📄 db/migrations/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Импорт моделей и URL конфигурации
from db.models import Base
from db.db_config import get_database_url  # ✅ автоматическое определение пути

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# Заменяем sqlalchemy.url на путь из db_config
config.set_main_option("sqlalchemy.url", get_database_url())

def run_migrations_offline():
    """Миграции в офлайн-режиме"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Миграции в онлайн-режиме"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()