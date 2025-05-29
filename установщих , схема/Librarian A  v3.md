librarian_ai/
├── main.py                        # 🚀 Главная точка запуска агента (CLI/Web/API)
│
├── config/                        # ⚙️ Конфигурационные файлы
│   ├── config.yaml                # Основная конфигурация путей, моделей, окружения
│   ├── e_full.yaml                # Полный паспорт агента: роль, авторизация, поведение
│   ├── remote.yaml                # Ключи API: OpenAI, YandexGPT, DeepSeek и др.
│   ├── quality_metrics.yaml       # Метрики качества ответов (точность, связность)
│   └── objectives.yaml            # Цели и KPI для автообучения и оптимизации
│
├── templates/                     # 🧰 Шаблоны генерации кода и конфигов
│   ├── main.py.tpl                # Шаблон главного модуля
│   ├── config.yaml.tpl            # Шаблон конфигурации агента
│   ├── base_llm.py.tpl            # Шаблон базового провайдера LLM
│   ├── loader.py.tpl              # Шаблон загрузчика файлов
│   └── readme.md.tpl              # Шаблон README для агентов
│
├── core/                          # 🧠 Ядро логики и обработки данных
│   ├── entity_extractor.py        # Простое извлечение сущностей (Natasha, spaCy)
│   ├── entity_extractor_advanced.py # Расширенное извлечение (словари, плагины, YAML)
│   ├── visualizer.py              # Визуализация графа сущностей (Plotly, Matplotlib)
│   ├── graph_tools.py             # Построение, анализ, кластеризация графа
│   └── connector_yadisk.py        # 🔄 Интеграция и синхронизация с Яндекс.Диском
│
├── llm/                           # 🤖 Модули для работы с LLM
│   ├── llm_router.py              # 🧠 SmartRouter — выбор лучшего ответа от моделей
│   ├── local_model.py             # Локальная обучаемая модель (ChatGLM, Mistral)
│   └── providers/                 # 📡 Подключаемые LLM-провайдеры
│       ├── base_llm.py            # Абстрактный класс для всех моделей
│       ├── openai_gpt.py          # GPT 3.5/4 от OpenAI
│       ├── yandex_gpt.py          # Модель от Яндекса
│       ├── deepseek.py            # DeepSeek API (альтернатива GPT от Китая)
│       ├── mistral_local.py       # Запуск локальной Mistral (GGUF, Transformers)
│       └── fallback_dummy.py      # Заглушка — используется при отсутствии подключения
│
├── knowledge/                     # 📚 Базы знаний
│   ├── vector_store/              # Векторная база (FAISS, Qdrant и др.)
│   ├── graph_cache/               # Кэш графов для быстрой визуализации
│   └── long_term_memory/          # Память агента: самообучение, кейсы
│
├── agents/                        # 🤖 Готовые агенты и их цепочки
│   ├── factory/                   # 🏗️ Генераторы шаблонных агентов
│   └── osint_plus/                # 🔍 Агент для сбора OSINT
│       ├── 1_collector.py       # Сбор открытых источников
│       ├── 1_enrichers.py         # Обогащение: гео, даты, ссылки
│       ├── 1_exporters.py         # Экспорт в JSON, базу или граф
│       └── 1_agent.yaml           # Паспорт OSINT-агента
│
├── storage/                       # 🗄️ Базы данных
│   └── librarian.db               # SQLite база: история, ответы, логика
│
├── cli/                           # 💻 Командная оболочка
│   └── agent_cli.py               # Запуск из консоли: /ask, /batch, /config
│
├── web/                           # 🌐 Web-интерфейс и API
│   ├── dashboard.py               # 🎛️ Flask/FastAPI панель с HTML-интерфейсом
│   └── endpoints/                 # REST API (ввод запроса, вывод ответа, логика)
│
├── telegram/                      # 📲 Бот в Telegram
│   └── bot.py                     # Бот-интерфейс (чат, команды, мониторинг)
│
├── utils/                         # 🔧 Утилиты и служебные скрипты
│   ├── logger.py                  # Цветное логирование, трассировка
│   ├── updater.py                 # Обновление моделей, конфигураций, self-learning
│   └── init_script.py             # Инициализация проекта, установка зависимостей
│
├── deploy/                        # 🚀 Автодеплой и CI/CD
│   ├── deploy.py                  # Заливка на GitHub, Я.Диск, CI-платформы
│   └── .env.template              # Шаблон секретов (.env для деплоя)
│
├── Makefile                       # 🧱 Сценарии сборки: make test / deploy / run
├── pyproject.toml                 # 📦 Описание зависимостей проекта (Poetry / PEP 518)
├── requirements.txt               # Пакеты pip (если не Poetry)
└── README.md                      # 📘 Документация проекта: установка, примеры, развитие
🧠 Что обеспечивает эта структура
Гибкое масштабирование: можно добавлять новых агентов, модели, внешние сервисы без переписывания ядра.

Удобство поддержки и обновлений: YAML/ENV-конфигурации, автообновления, SmartRouter.

Производственный уровень: CI/CD, деплой, телеметрия, API-интерфейсы.

Возможность интеграции с 1С, Telegram, внешними CRM и аналитикой.