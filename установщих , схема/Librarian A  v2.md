# 📁 Проект: Librarian AI (прототип агента-библиотекаря)

# ┌────────────────────────────────────────────┐
# |     Структура директорий и файлов v0.1    |
# └────────────────────────────────────────────┘

**Librarian AI **/
├librarian_ai/
├── main.py                      # 🚀 Главный вход в систему (через CLI/Web/Trigger)
├── config/
│   ├── config.yaml              # Общая конфигурация (пути, LLM, диски)
│   ├── e_full.yaml              # Паспорт агента
│   └── remote.yaml              # Доступ к облачным LLM (API ключи, токены)
├── templates/                   # Шаблоны для генерации агентов и их компонентов
│   ├── *.tpl
├── core/
│   ├── entity_extractor.py
│   ├── entity_extractor_advanced.py
│   ├── visualizer.py
│   ├── graph_tools.py
│   └── connector_yadisk.py      # 🔄 Интеграция с Яндекс.Диском
├── llm/
│   ├── llm_router.py            # 🧠 Маршрутизатор между локальными и внешними ИИ
│   ├── local_model.py           # 🏠 Собственная обучаемая модель (LLM или FastText/Transformer)
│   └── providers/
│       ├── openai_gpt.py          # ✅
│       ├── yandex_gpt.py          # ✅
│       ├── deepseek.py            # ✅
│       ├── mistral_local.py       # ⚙️
│       ├── fallback_dummy.py      # ✅
│       └── base_llm.py            # 1 Общая абстракция
├── knowledge/
│   ├── vector_store/            # Векторная база знаний
│   ├── graph_cache/
│   └── long_term_memory/        # Память для автотренировки модели
├── agents/
│   ├── factory/
│   └── osint_plus/
│       ├── 1_collector.py
│       ├── 1_enrichers.py
│       ├── 1_exporters.py
│       └── 1_agent.yaml
├── storage/
│   └── librarian.db             # SQLite база
├── cli/
│   └── agent_cli.py
├── web/
│   ├── dashboard.py             # 🎛️ Веб-интерфейс (на Flask/FastAPI)
│   └── endpoints/               # REST API
├── telegram/
│   └── bot.py                   # Телеграм-бот
├── utils/
│   ├── logger.py
│   ├── updater.py               # 🔁 Автообновление моделей и скриптов
│   └── init_script.py           # Первичная инициализация
└── README.md


роект: librarian_ai/
Librarian AI — модульная архитектура для интеллектуального агента, поддерживающего локальную работу, подключение внешних LLM (в т.ч. GPT, YandexGPT), обработку текстов, граф знаний и автоматическое самообучение.

🔧 Главная логика
css
Копировать
Редактировать
├── main.py
main.py — 🚀 главная точка входа в систему. Запускает CLI, Web-интерфейс или другие режимы (batch, agent mode, API).

⚙️ Конфигурация
arduino
Копировать
Редактировать
├── config/
│   ├── config.yaml
│   ├── e_full.yaml
│   └── remote.yaml
config.yaml — основная конфигурация: пути, используемые модели, включенные модули.

e_full.yaml — описание текущего агента (название, роль, ограничения, флаги).

remote.yaml — API-ключи, токены, настройки доступа к внешним LLM (OpenAI, Yandex).

🧰 Шаблоны генерации
Копировать
Редактировать
├── templates/
│   ├── *.tpl
main.py.tpl, loader.py.tpl и др. — шаблоны для генерации новых агентов, конфигураций и логики.

Используются скриптом install.py или через команду agent create.

🧠 Ядро обработки
Копировать
Редактировать
├── core/
│   ├── entity_extractor.py
│   ├── entity_extractor_advanced.py
│   ├── visualizer.py
│   ├── graph_tools.py
│   └── connector_yadisk.py
entity_extractor.py — базовое извлечение сущностей (Natasha, spaCy).

entity_extractor_advanced.py — расширенная версия: поддержка плагинов, словарей, кэширования, YAML-конфигураций.

visualizer.py — визуализация сущностей в графе (Matplotlib, Plotly).

graph_tools.py — работа с графами: экспорт, фильтрация, аналитика.

connector_yadisk.py — 🔄 подключение к Яндекс.Диску, выгрузка и загрузка данных, синхронизация.

🤖 Модули LLM
Копировать
Редактировать
├── llm/
│   ├── llm_router.py
│   ├── local_model.py
│   └── providers/
│       ├── gpt_openai.py
│       ├── yandex_gpt.py
│       └── fallback_dummy.py
llm_router.py — маршрутизатор: направляет запрос к нужной модели в зависимости от доступности.

local_model.py — локальная LLM (может быть FastText, HuggingFace, ChatGLM).

providers/ — адаптеры для внешних ИИ:

gpt_openai.py — подключение к GPT 3.5/4 через OpenAI API.

yandex_gpt.py — подключение к YandexGPT.

fallback_dummy.py — ответ-заглушка, если LLM недоступны.

📚 Хранилище знаний
Копировать
Редактировать
├── knowledge/
│   ├── vector_store/
│   ├── graph_cache/
│   └── long_term_memory/
vector_store/ — база векторных эмбеддингов.

graph_cache/ — кэш графов сущностей.

long_term_memory/ — 🧠 база для обучения своей LLM или сохранения ключевых смыслов.

🧬 Агенты
Копировать
Редактировать
├── agents/
│   ├── factory/
│   └── osint_plus/
│       ├── 1_collector.py
│       ├── 1_enrichers.py
│       ├── 1_exporters.py
│       └── 1_agent.yaml
factory/ — шаблоны для генерации новых агентов.

osint_plus/ — готовый OSINT-агент:

1_collector.py — сбор данных из открытых источников.

1_enrichers.py — обогащение через API, гео-данные, нормализация.

1_exporters.py — экспорт в базы, JSON, Graph.

1_agent.yaml — описание возможностей агента.

🗄️ Хранилище
pgsql
Копировать
Редактировать
├── storage/
│   └── librarian.db
librarian.db — SQLite база: лог запросов, результаты, агентные сессии.

🖥️ CLI + Web
Копировать
Редактировать
├── cli/
│   └── agent_cli.py

├── web/
│   ├── dashboard.py
│   └── endpoints/
agent_cli.py — командная оболочка: запуск, отладка, диалог с агентом.

dashboard.py — простой веб-интерфейс для работы через браузер.

endpoints/ — REST API для подключения из внешних сервисов.

📲 Телеграм
Копировать
Редактировать
├── telegram/
│   └── bot.py
bot.py — интерфейс агента через Telegram: чат, команды, изображения.

🧩 Утилиты
Копировать
Редактировать
├── utils/
│   ├── logger.py
│   ├── updater.py
│   └── init_script.py
logger.py — логгирование, в том числе цветное в терминал.

updater.py — автоматическое обновление моделей, плагинов, конфигураций.

init_script.py — первичная установка окружения, папок, примеров.

📘 Документация
Копировать
Редактировать
└── README.md
Основная документация по установке, запуску и настройке проекта.