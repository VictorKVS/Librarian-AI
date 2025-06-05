# 📁 Проект: Librarian AI (прототип агента-библиотекаря)

# ┌────────────────────────────────────────────┐
# |     Структура директорий и файлов v0.1    |
# └────────────────────────────────────────────┘

**Librarian AI **/

├── main.py                        # Главная точка запуска агента
├── install.py                     # 🚀 Установщик: создаёт структуру проекта
├── templates/                     # 🧹 Шаблоны начальных файлов
│       ├── main.py.tpl               # Шаблон main.py
│       ├── config.yaml.tpl           # Шаблон конфигурации 
│       ├── base_llm.py.tpl           # Шаблон базового LLM
│       ├── loader.py.tpl             # Шаблон загрузчика 
│       └── readme.md.tpl             # Шаблон README
├── config/ 
│       ├── config.yaml               # Конфигурация агента (LLM, пути, включения)
│       └── e_full.yaml               # 📋 Полное описание агента (AgentDNA) 
├── llm/ 
│      ├── base.py                   # Базовой интерфейс LLM 
│      ├─  yandex_gpt.py             # Адаптер для YandexGPT
│      ├── local_chatglm.py          # Адаптер для локальной ChatGLM
│      ├── deep_pavlov.py            # Адаптер DeepPavlov 
│      └── llm_router.py             # 🧠 Маршрутизатор между моделями 
├── core/ 
│      ├── loader.py                 # Загрузка документов 
|      ├── parser.py                 # Извлечение текста и метаданных 
│      ├── classifier.py             # Тематическая классификация 
│      ├── embedder.py              # Векторизация (BERT, etc) 
│      ├── storage.py               # Сохранение в базу данных 
│      ├── retriever.py             # 🔍 Семантический поиск (RAG) 
│      └── re_ranker.py             # 🔁 Re-ranking документов по релевантности 
├── graph/
│      └── graph_store.py           # 📊 Обработка графа знаний (GraphRAG) 
├── db/ 
│      └── librarian.db              # SQLite база данных 
├── knowledge/ 
│        ├ ── vector_store/            # Векторная база знаний 
│        └── graph_cache/             # Кэш графовой структуры
├── utils/ 
│          └── logger.py                # Логирование и диагностика 
├── cli/ 
│           └── agent_cli.py             # CLI-интерфейс для запросов 
├── telegram/
│            └── bot.py                   # Telegram-бот (опционально) 
├── agents/ 
│           ├── factory/                 # 🏠 Шаблоны и цепочки агентов 
│           └── osint_plus/              # 🛠️ OSINT+ агент 
│                         ├── collector.py        # Сбор информации 
│                         ├── enrichers.py        # Обогащение данных 
│                         ├── exporters.py        # Экспорт в JSON/БД 
│                         └── agent.yaml          # Паспорт описания OSINT агента 
└── README.md                    # Основная документация
# Пример запуска:
# python main.py --mode batch --source ./data/news/
# python cli/agent_cli.py --query "Что известно о компании X?"