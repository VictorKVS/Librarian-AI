# 📘 ENI (Event/Note Index) — Librarian AI

> Журнал событий, решений и изменений проекта Librarian AI

---

## 🧱 Архитектура проекта

* 📆 2025-06-11: Подтверждена структура каталогов (см. `proekt_librarian_ai.md`)
* ✅ Стартовые модули: loader, parser, chunker, embedder, NER (заглушка), graph\_builder
* 🧩 Принято использовать: FastAPI + Celery + SQLite + Redis
* 📌 Используемые NLP-инструменты: spaCy, SentenceTransformers, custom NER

---

## 📅 Хронология ключевых событий

### Июнь 2025

* ✅ `create_tables.py`: генерация базы `librarian.db`
* ✅ `ingest_and_index.py`: пайплайн загрузки и сохранения документа
* ✅ Добавлены модули: `loader.py`, `parser.py`, `chunker.py`
* 📌 Решение: использовать `TextParser` с фильтрацией HTML, email, URL
* 🧠 План: добавить Presidio/regex для расширенного NER

### Июль 2025

* 🧪 Завершён тестовый прогон на `🔗 1.docx` → база сформирована
* ✅ Подключён API (documents.py) с Celery-фоном
* ✅ `async_tasks.py`: асинхронная задача обработки документа
* ✅ Обработка чанков, сущностей и эмбеддингов в базе
* 📌 Принято: завершить фазу `v0.1-mini`
* 📌 Решение: начать формирование ENI (текущий файл)

---

## 🚧 Открытые вопросы / TODO

* 🔄 Интеграция продвинутого NER (spaCy/Natasha/Presidio)
* 🔗 Визуализация графа знаний
* 🧪 Добавить модульные тесты (tests/)
* 🔍 Разработка reasoning-модуля (`v0.3`)

---

## 🗂️ Согласования и принятые решения

* 📎 Все согласования фиксируются в `proekt_librarian_ai.md`
* 🔖 Все патчи и изменения сопровождаются коммитами с тегами `feat:`, `fix:`, `docs:`
* 📌 Использовать ENI как базу для автообновления changelog'а

---

## 📍 Контрольные точки (Milestones)

* ✅ v0.1-mini завершён: 2025-07-09
* ⏳ v0.2-extended — расширенный пайплайн, улучшенный NER, связи
* ⏳ v0.3-semantic — reasoning, генерация аннотаций, sem.graph

---

## 🧩 Связанные файлы

* `proekt_librarian_ai.md`
* `roadmap.md`
* `Readme.md`
* `create_tables.py`, `ingest_and_index.py`, `async_tasks.py`

---

📌 ENI обновляется вручную или автоматически при коммитах/шаблонах.
