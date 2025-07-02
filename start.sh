# 📄 Файл: start.sh
# 📂 Путь: / (корень проекта)
# 📌 Назначение: При запуске контейнера применяет миграции Alembic и запускает main.py

#!/bin/bash

echo "⏳ Применение миграций..."
alembic upgrade head

echo "🚀 Запуск приложения..."
exec python main.py