librarian_ai/

├── auth/
│   ├── jwt_handler.py
│   ├── oauth2.py
│   └── dependencies.py



├── agents/                        # 🤖 Готовые агенты и цепочки
│   ├── factory/                   # 🏗️ Генераторы шаблонных агентов
│   └── osint_plus/                # 🔍 OSINT-агент: сбор, enrich, экспорт
│       ├── 1_collector.py
│       ├── 1_enrichers.py
│       ├── 1_exporters.py
│       └── 1_agent.yaml

├── api/                           # 🌐 API модули FastAPI
│   ├── files.py                   # Обработка загрузки файлов
│   └── email.py                   # Заглушка для email-загрузки (будет расширяться)

├── cli/                           # 💻 CLI-интерфейс
│   └── agent_cli.py               # Взаимодействие из терминала

├── config/                        # ⚙️ Конфигурационные файлы
│   ├── config.yaml                # Пути, LLM, переменные
│   ├── e_full.yaml                # Паспорт агента
│   └── remote.yaml                # API-ключи (OpenAI, Yandex и т.п.)

├── core/                          # 🧠 Ядро обработки данных
│   ├── embedder.py                # Векторизация текста
│   ├── entity_extractor.py        # Простое извлечение (spaCy, Natasha)
│   ├── entity_extractor_advanced.py # Расширенное извлечение с плагинами
│   ├── graph_tools.py             # Построение графов, фильтрация, кластеризация
│   ├── librarian_ai.py            # Исполнитель агентной логики
│   ├── loader.py                  # Загрузка и анализ файлов
│   └── parser.py                  # Разметка, метаданные

├── db/                            # 🗄️ База данных и ORM-модели
│   ├── models.py                  # SQLAlchemy модели (Session, Entity, Doc и пр.)
│   └── storage.py                 # Работа с PostgreSQL, SQLite, pgvector

├── deploy/                        # 🚀 Скрипты публикации и автозапуска
│   ├── deploy.py                  # GitHub/Я.Диск/CI-интеграция
│   └── .env.template              # Шаблон конфигурации переменных окружения

├── docs/                          # 📘 Документация проекта (MkDocs или Sphinx)
│   ├── index.md
│   └── architecture.md

├── graph/                         # 📈 Графы знаний и связи
│   └── graph_store.py             # Работа с GEXF и NetworkX

├── knowledge/                     # 📚 Хранилище знаний, памяти
│   ├── graph_cache/               # Кэш графов
│   ├── vector_store/              # FAISS/Qdrant база
│   └── long_term_memory/          # Постоянная память (MemoryItem)

├── llm/                           # 🤖 Работа с моделями LLM
│   ├── llm_router.py              # Умный маршрутизатор
│   ├── llm_router_pro.py          # Расширенная версия с анализом качества
│   ├── local_model.py             # Локальные модели (ChatGLM, GGUF, Mistral)
│   └── providers/
│       ├── base_llm.py            # Абстрактный класс для провайдеров
│       ├── deepseek.py
│       ├── fallback_dummy.py
│       ├── openai_gpt.py
│       ├── yandex_gpt.py
│       └── mistral_local.py       # ⚙️ Подключение через Ollama

├── storage/                       # 📦 Альтернативная БД (SQLite)
│   └── librarian.db

├── telegram/                      # 📲 Телеграм-бот
│   └── bot.py                     # Чат-бот на основе aiogram

├── templates/                     # 🧰 Шаблоны генерации
│   ├── main.py.tpl
│   ├── config.yaml.tpl
│   ├── base_llm.py.tpl
│   ├── loader.py.tpl
│   └── readme.md.tpl

├── tests/                         # ✅ Авто-тесты
│   ├── test_llm_router.py
│   ├── test_extractor.py
│   └── test_models.py

├── utils/                         # 🔧 Вспомогательные скрипты
│   ├── logger.py                  # Логгирование
│   ├── updater.py                 # Автообновления и retraining
│   ├── init_script.py             # Инициализация структуры
│   ├── file_utils.py              # Рекурсивная обработка директорий
│   ├── ocr_cache.py               # Кэширование OCR
│   ├── security.py                # MIME и вирусные фильтры
│   ├── metrics.py                 # Бенчмаркинг, замеры
│   └── add_headers.py             # Добавление заголовков в *.py

├── web/                           # 🌍 FastAPI-интерфейс
│   ├── dashboard.py               # Основной сервер (uvicorn)
│   └── endpoints/                 # REST API

├── benchmark/                     # 📊 Модули для измерений
│   ├── latency_test.py
│   ├── quality_score.py
│   └── memory_benchmark.py

├── deploy_gui.py                  # 🖱️ PyQt-интерфейс деплоя
├── docker-compose.yaml            # 🐳 Контейнеризация (Postgres, Qdrant, Redis, API)
├── Dockerfile.dockerfile          # 🐍 Docker сборка web/worker
├── install.py                     # 🛠️ Автогенерация проекта
├── start.sh                       # 🚀 Старт: Alembic + main.py
├── pyproject.toml                 # 📦 Poetry или pip-зависимости
├── Makefile                       # 🔁 Команды make run/install/test
└── README.md                      # 🧾 Описание, инструкция, цели
