librarian_ai/
├── api
    ├──files.py
├── main.py                        # 🚀 Главная точка запуска агента (CLI/Web/API)
│
├── config/                        # ⚙️ Конфигурационные файлы
│   ├── config.yaml                # Основная конфигурация путей, моделей, окружения
│   │   ├── remote.yaml                # Ключи API: OpenAI, YandexGPT, DeepSeek и др.
│   
│
├── templates/                     # 🧰 Шаблоны генерации кода и конфигов
│   
│
├── core/  
    ├──  embedder.py                  # 🧠 Ядро логики и обработки данных
│   ├── entity_extractor.py        # Простое извлечение сущностей (Natasha, spaCy)
│   ├── entity_extractor_advanced.py # Расширенное извлечение (словари, плагины, YAML)
│   ├──librarian_ai.py
    ├──     loader.py
    ├──      parser.py
│   ├── graph_tools.py             # Построение, анализ, кластеризация графа

├── db
├── graph
    ├──  graph_store.py
├── Librarian-AI 
     ├──   README.md
│   
│
├── llm/                           # 🤖 Модули для работы с LLM
│   ├── llm_router.py              # 🧠 SmartRouter — выбор лучшего ответа от моделей
        llm_router_pro.py
│   ├── local_model.py             # Локальная обучаемая модель (ChatGLM, Mistral)
│   └── providers/                 # 📡 Подключаемые LLM-провайдеры
│       ├── base_llm.py            # Абстрактный класс для всех моделей         
│       ├── openai_gpt.py          # GPT 3.5/4 от OpenAI
│       ├── yandex_gpt.py          # Модель от Яндекса
│       ├── deepseek.py            # DeepSeek API (альтернатива GPT от Китая)
│       ├──
│       └── fallback_dummy.py      # Заглушка — используется при отсутствии подключения
├──   utils
│
├── knowledge/                     # 📚 Базы знаний
│   ├── vector_store/              # Векторная база (FAISS, Qdrant и др.)
│   ├── graph_cache/               # Кэш графов для быстрой визуализации
│   └── long_term_memory/          # Память агента: самообучение, кейсы
│
├── agents/                        # 🤖 Готовые агенты и их цепочки
│   ├── factory/                   # 🏗️ Генераторы шаблонных агентов
│   └── osint_plus/                # 🔍 Агент для сбора OSINT
│       
│
├── storage/                       # 🗄️ Базы данных
│   └
│
├── cli/                           # 💻 Командная оболочка
├── tests
    ├──  test_llm_router_pro.py
│
├── web/                           # 🌐 Web-интерфейс и API
│  
│
├── telegram/                      # 📲 Бот в Telegram
│   └──
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
 
├deploy_gui.py
  install.p

└── README.md                      # 📘 Документация проекта: установка, примеры, развитие
🧠 Что обеспечивает эта структура
Гибкое масштабирование: можно добавлять новых агентов, модели, внешние сервисы без переписывания ядра.

Удобство поддержки и обновлений: YAML/ENV-конфигурации, автообновления, SmartRouter.

Производственный уровень: CI/CD, деплой, телеметрия, API-интерфейсы.

Возможность интеграции с 1С, Telegram, внешними CRM и аналитикой.