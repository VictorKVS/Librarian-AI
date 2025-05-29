📁 Librarian_ai/
├── main.py                        # 🚀 Главная точка запуска агента (CLI, Web, API)
├── api
    ├──files.py
│   └── email.py                 # 🔌 Заглушка API /email/upload/


├── docker-compose.yaml  
├── deploy_gui.py
├── Dockerfile.dockerfile
├── install.py
├── start.sh

├── config/                        # ⚙️ Конфигурационные файлы
│   ├── config.yaml                # Основная конфигурация путей, моделей, режимов
│   ├── e_full.yaml                # 📋 Паспорт агента (роль, поведение, ограничения)
│   └── remote.yaml                # 🔐 API-ключи (OpenAI, YandexGPT и др.)

├── templates/                     # 🧰 Шаблоны генерации агентов, CLI, README
│   ├── main.py.tpl
│   ├── config.yaml.tpl
│   ├── base_llm.py.tpl
│   ├── loader.py.tpl
│   └── readme.md.tpl

├── core/                          # 🧠 Ядро логики извлечения и анализа
│   ├── entity_extractor.py               # Простое извлечение сущностей
│   ├── entity_extractor_advanced.py     # Расширенное извлечение (словари, плагины)
│   ├── embedder.py                      # Векторизация текстов
│   ├── graph_tools.py                   # Работа с графами (анализ, фильтрация)
│   ├── visualizer.py                    # Визуализация графа (Plotly, NetworkX)
│   ├── parser.py                        # Парсинг и извлечение метаданных
│   ├── loader.py                        # Загрузка и предобработка документов
│   ├── librarian_ai.py                  # Главный исполнитель логики агента
│   └── connector_yadisk.py              # 🔄 Интеграция с Яндекс.Диском

├── db/                                  # 📦 Модели и инициализация БД
│   ├── models.py                        # SQLAlchemy ORM (PostgreSQL, SQLite)
│   └── storage.py                       # Сессия БД, init, поддержка pgvector

├── graph/                               # 📈 Работа с графом знаний
│   └── graph_store.py                   # GraphRAG-хранилище, GEXF, Cache

├── llm/                                 # 🤖 Интеграция с LLM и маршрутизация
│   ├── llm_router.py                    # SmartRouter — выбор лучшей модели
│   ├── llm_router_pro.py                # Расширенная версия с кешами, цепочками
│   ├── local_model.py                   # Локальная модель (ChatGLM, Mistral и др.)
│   └── providers/                       # 📡 Провайдеры внешних моделей
│       ├── base_llm.py                  # Абстрактный интерфейс для всех моделей
│       ├── openai_gpt.py                # Подключение к OpenAI GPT
│       ├── yandex_gpt.py                # Подключение к YandexGPT
│       ├── deepseek.py                  # DeepSeek API
│       ├── fallback_dummy.py            # Заглушка при недоступности
│       └── mistral_local.py             # Локальный запуск Mistral/GGUF

├── knowledge/                           # 🧠 Хранилище знаний, памяти и связей
│   ├── vector_store/                    # Векторная база знаний (FAISS, Qdrant)
│   ├── graph_cache/                     # Кэш графов (для визуализации)
│   └── long_term_memory/                # Память агента, примеры, тренировки

├── agents/                              # 🤖 Готовые агенты и цепочки
│   ├── factory/                         # Шаблоны генерации новых агентов
│   └── osint_plus/                      # Пример агента (OSINT-бот)
│       ├── 1_collector.py               # Сбор данных
│       ├── 1_enrichers.py               # Обогащение
│       ├── 1_exporters.py               # Экспорт (JSON, GEXF, DB)
│       └── 1_agent.yaml                 # Паспорт OSINT-агента

├── storage/                             # 🗄️ Локальные базы
│   └── librarian.db                     # SQLite (альтернатива PostgreSQL)

├── cli/                                 # 💻 Командная оболочка
│   └── agent_cli.py                     # Быстрый запуск команд и диагностики

├── web/                                 # 🌐 Web-интерфейс и API
│   ├── dashboard.py                     # Панель управления (Flask/FastAPI)
│   └── endpoints/                       # REST API (входные точки)

├── telegram/                            # 📲 Telegram-интерфейс
│   └── bot.py                           # Чат-бот: чат, генерация, ответы

├──  utils/
│       ├── logger.py               # 📋 Централизованное логирование
│       ├── updater.py              # 🔁 Автообновление моделей, плагинов, данных
│       ├── init_script.py          # 🧱 Установка структуры проекта, env, Alembic
│       ├── file_utils.py           # 📂 Работа с директориями, проверка форматов, MIME
│       ├── ocr_cache.py            # 🧠 Кэширование результатов OCR
│       ├── security.py             # 🔒 Проверка размеров, вирусов, MIME-типов
│       ├── metrics.py              # 📊 Отправка метрик, бенчмаркинг
│       └── add_headers.py          # 🧾 Генерация заголовков в файлах по шаблону

├── deploy/                              # 🚀 Автодеплой, GitHub, YandexDisk
│   ├── deploy.py                        # Скрипт заливки и сохранения
│   └── .env.template                    # Шаблон с токенами и паролями

├── deploy_gui.py                        # 🖱️ GUI-интерфейс деплоя (PyQt5)
├── install.py                           # Установка проекта, генерация структуры

├── docker-compose.yaml                  # 🐳 Запуск Redis, PostgreSQL, Qdrant, API
├── pyproject.toml                       # 📦 Метаданные проекта и зависимости
├── Makefile                             # 🔧 Команды make (install, deploy, test)

├── benchmark/                           # 📊 Тесты latency, качества, нагрузки
│   ├── latency_test.py
│   ├── quality_score.py
│   └── memory_benchmark.py

├── docs/                                # 📘 Документация (Sphinx / MkDocs)
│   ├── index.md
│   ├── architecture.md
│   ├── agent_examples.md
│   └── api_reference.md

├── tests/                               # ✅ Модульные и интеграционные тесты
│   ├── test_llm_router.py
│   ├── test_extractor.py
│   └── test_models.py

└── README.md                            # 📄 Документация, цели, лицензия, лого


ключённые улучшения:
Категория	Поддержка
PostgreSQL + pgvector	✅
Redis / Qdrant	✅
Яндекс.Диск	✅
GitHub CI / Makefile	✅
Telegram	✅
Web UI / API	✅
Автообновление моделей	✅
Benchmark-модуль	✅
Визуализация графов	✅

