Librarian_ai/
├──.venv/
     ├── Include/
     ├── Lib/
         ├──site-packages/
             ├──pip/
                ├─__pycache__/
                │   ├─__init__.cpython-313.pyc
                │   ├─__main__.cpython-313.pyc
                │   ├─__pip-runner__.cpython-313.pyc
                ├─ _internal/
                │        ├─  _init__.cpython-313.pyc
                │        ├─  build_env.cpython-313.pyc
                │        ├─  cache.cpython-313.pyc
                │        ├─  configuration.cpython-313.pyc
                │        ├─  exceptions.cpython-313.pyc
                │        ├─  main.cpython-313.pyc
                │        ├─  pyproject.cpython-313.pyc
                │        ├─  self_outdated_check.cpython-313.pyc
                │        └──  wheel_builder.cpython-313.pyc
                ├─  __pycache__ /
                │       ├─ __init__.cpython-313.pyc
                │       ├─  autocompletion.cpython-313.pyc
                │       ├─  base_command.cpython-313.pyc
                │       ├─  cmdoptions.cpython-313.pyc
                │       ├─  command_context.cpython-313.pyc
                │       ├─  index_command.cpython-313.pyc
                │       ├─  main.cpython-313.pyc
                │       ├─  main_parser.cpython-313.pyc
                │       ├─  parser.cpython-313.pyc
                │       ├─  progress_bars.cpython-313.pyc
                │       ├─  req_command.cpython-313.pyc
                │       └── status_codes.cpython-313.pyc
                ├─      


      main.cpython-313.pyc
├── agents/                        # 🤖 Готовые агенты и их цепочки
│   ├── factory/                   # 🏗️ Генераторы шаблонных агентов
│   └──osint_plus-                # 🔍 Агент для сбора OSINT

├── api
│     ├──__pycache__
│     │        └───files.cpython-313.pyc
│     ├── email.py
│     ├── files.py
│     └── process_router.py
│ 
├── cli/                           # 💻 Командная оболочка
    ├──agent_cli.py
├── tests
    
    └──  test_llm_router_pro.py

├── config/                        # ⚙️ Конфигурационные файлы
│   ├── config.yaml                # Основная конфигурация путей, моделей, окружения
│   └── remote.yaml                # Ключи API: OpenAI, YandexGPT, DeepSeek и др.
│   
├── core/  
│   ├──  __pycache__
│   │       └──   loader.cpython-313.pyc
│   ├──  embedder.py                  # 🧠 Ядро логики и обработки данных
│   ├── entity_extractor.py        # Простое извлечение сущностей (Natasha, spaCy)
│   ├── entity_extractor_advanced.py # Расширенное извлечение (словари, плагины, YAML)
│   ├── graph_tools.py             # Построение, анализ, кластеризация графа
│   ├── librarian_ai.py
│   ├── loader.py
│   ├── parser.py
  
├── db
    ├── models.py  
    ├──storage.py
├── graph
    ├──  graph_store.py
├── knowledge/                     # 📚 Базы знаний
│   ├── graph_cache/              # Кэш графов для быстрой визуализации
│   └── vector_store/            # Векторная база (FAISS, Qdrant и др.)
│   ├─long_term_memory/           # Память агента: самообучение, кейсы 
│
├── Librarian-AI 
     ├──   README.md

├── llm/                           # 🤖 Модули для работы с LLM
│   ├── llm_router.py              # 🧠 SmartRouter — выбор лучшего ответа от моделей
│   ├──    llm_router_pro.py
│   ├── local_model.py             # Локальная обучаемая модель (ChatGLM, Mistral)
│   │ 
│   └── providers/                 # 📡 Подключаемые LLM-провайдеры
│       ├── base_llm.py            # Абстрактный класс для всех моделей         
│       ├── deepseek.py            # DeepSeek API (альтернатива GPT от Китая)
│       ├── fallback_dummy.py      # Заглушка — используется при отсутствии подключения
│       ├── openai_gpt.py          # GPT 3.5/4 от OpenAI
│       └──  yandex_gpt.py          # Модель от Яндекса
├── storage/                       # 🗄️ Базы данных
│   └       
├── telegram/                      # 📲 Бот в Telegram
│   └──
├── templates/                     # 🧰 Шаблоны генерации кода и конфигов
│   │   
│       
├──  tests
│  └──test_llm_router_pro.py
├──   utils
│      ├── email_utils.py
│      ├──file_utils.py
│
├── web/                           # 🌐 Web-интерфейс и API
│  
├── deploy_gui.py
├── docker-compose.yaml
├── Dockerfile.dockerfile
│
├── install.py
│
├── main.py                        # 🚀 Главная точка запуска агента (CLI/Web/API)
│
├──README.md                      # 📘 Документация проекта: установка, примеры, развитие
│
├── start.sh
├──Untitled-1.yaml


🧠 Что обеспечивает эта структура
Гибкое масштабирование: можно добавлять новых агентов, модели, внешние сервисы без переписывания ядра.

Удобство поддержки и обновлений: YAML/ENV-конфигурации, автообновления, SmartRouter.

Производственный уровень: CI/CD, деплой, телеметрия, API-интерфейсы.

Возможность интеграции с 1С, Telegram, внешними CRM и аналитикой.