# Архитектура системы Librarian-AI

## Обзор компонентов

1. **FastAPI API** (`api/`)
   - Файловый сервис (`files.py`)
   - Семантический поиск (`search.py`)
   - Генерация аннотаций (`summary.py`)
   - Почтовый сервис (`email.py`) и т.д.

2. **Ядро (core/)**  
   - **Парсинг текстов** (`parser/chunker.py`, `parser/loader.py`, `parser/parser.py`)  
   - **Обработка документов** (`processor/document_processor.py`, `processor/retriever.py`)  
   - **Векторизация** и **поиск** (`tools/embedder.py`, `tools/semantic_search.py`)  
   - **Генерация аннотаций** (`tools/summary_generator.py`)  
   - **Фоновые задачи** (`tools/async_tasks.py`)  
   - **Извлечение сущностей** (`tools/extractor.py`)  
   - **Граф знаний** (`tools/graph_tools.py`)  
   - **OCR-кеширование** (если потребуется) и другие утилиты

3. **DB и хранение** (`db/`)  
   - SQLAlchemy-модели (`models.py`)  
   - Alembic-миграции (`migrations/`)  
   - Логика доступа к БД (`storage.py`)

4. **LLM-аналитик** (`librarian_ai/llm/`)  
   - Провайдеры (Gigachat, OpenRouter, YandexGPT, Mistral, LM Studio и др.)  
   - Маршрутизатор запросов к нужному LLM  
   - Локальный доступ к модели (при необходимости)

5. **Утилиты** (`utils/`)  
   - Работа с файлами (`file_utils.py`)  
   - Отправка почты (`email_utils.py`)  
   - Логирование (`logger.py`)  
   - Метрики (`metrics.py`)  
   - Безопасность загрузки файлов (`security.py`)  
   - Кэш OCR (`ocr_cache.py`)  
   - Расстановка заголовков в коде (`add_headers.py`)  
   - Менеджер миграций/обновлений (`updater.py`)

6. **Telegram-бот** (`telegram/bot.py`)

7. **Второй Web-сервер (дашборд)** (`web/dashboard.py`, `web/endpoints/`)

## Поток данных

1. Клиент отправляет документ через `/files/upload`  
2. Core/parser загружает и разбивает на чанки (`chunker`, `loader`)  
3. При сохранении вызывается `tools/embedder`, создаются эмбеддинги и сохраняются в векторный индекс  
4. При запросе `/search` или `/summary` используется `processor/retriever` и `tools/summary_generator`  
5. Конечный результат возвращается пользователю в виде JSON или файла  

## Масштабирование и развёртывание

- **Docker-Compose**: PostgreSQL, Redis (для Celery), Qdrant  
- **К8s-файлы**: (создать позже по необходимости)  
- **CI/CD**: GitHub Actions / GitLab CI — сборка, тесты, линты, развёртывание  
- **Мониторинг**: Prometheus/Grafana для метрик, Sentry для логирования ошибок 