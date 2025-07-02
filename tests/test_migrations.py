# 📄 tests/test_migrations.py
# Тестирование Alembic миграций (upgrade и downgrade)

import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
import os
import shutil

# Временная БД для тестов
TEST_DB_URL = "sqlite:///tests/test_migrations.sqlite"

@pytest.fixture(scope="module")
def alembic_config():
    # Копия alembic.ini с другим URL
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return config

@pytest.fixture(scope="function")
def clean_test_db():
    if os.path.exists("tests/test_migrations.sqlite"):
        os.remove("tests/test_migrations.sqlite")
    yield
    if os.path.exists("tests/test_migrations.sqlite"):
        os.remove("tests/test_migrations.sqlite")

def test_upgrade_downgrade(alembic_config, clean_test_db):
    # Применяем миграции
    command.upgrade(alembic_config, "head")

    engine = create_engine(TEST_DB_URL)
    inspector = inspect(engine)

    # Проверка: таблицы созданы
    tables = inspector.get_table_names()
    assert "session" in tables or len(tables) > 0

    # Откат
    command.downgrade(alembic_config, "base")
    inspector = inspect(engine)
    assert inspector.get_table_names() == []
