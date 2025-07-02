# 📄 db/db_config.py
# Автоматический выбор пути к базе данных в зависимости от среды исполнения

import os
import platform
import socket

def get_database_url() -> str:
    # 1. Проверка переменной окружения — приоритетнее всего
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # 2. Определение по hostname (например, Google Colab)
    hostname = socket.gethostname()
    if "colab" in hostname or "instance" in hostname:
        return "sqlite:////content/drive/MyDrive/librarian.db"

    # 3. Проверка ОС или путей монтирования (например, Яндекс Диск)
    if platform.system() == "Linux" and os.path.exists("/mnt/yandex-disk/"):
        return "sqlite:////mnt/yandex-disk/librarian.db"

    # 4. Значение по умолчанию (локальный запуск с флешки)
    return "sqlite:///db/librarian.db"

# Пример использования
if __name__ == "__main__":
    print(f"🔌 База данных подключена по пути: {get_database_url()}")

"""
📄 db/db_config.py
Назначение:
Автоматически определяет путь к базе данных (SQLite или другой) в зависимости от среды:

Читает DATABASE_URL из переменных окружения (если задана)

Распознаёт Google Colab, Яндекс Диск, флешку

Возвращает корректный sqlalchemy.url для SQLAlchemy или Alembic

Используется в:

storage.py — для подключения к БД

migrations/env.py — для Alembic миграций

Преимущество:
Позволяет запускать проект на любой машине или носителе без изменения кода.
Место	Стратегия подключения
Флешка	SQLite: sqlite:///db/librarian.db
Яндекс Диск	SQLite или PostgreSQL с другим путём
Google Colab	sqlite:////content/... или GDrive
Alembic	URL из переменной DATABASE_URL
"""