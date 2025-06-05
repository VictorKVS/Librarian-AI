# deploy/.env.template
# Пример:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=librarian_db
DB_USER=librarian
DB_PASSWORD=secretpass

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Qdrant/Vector store
QDRANT_HOST=localhost