"""
Librarian-AI 🧠 — Главная точка входа

Этот модуль запускает FastAPI-приложение и Telegram-бота через адаптированную архитектуру AdvancedApplication.
Структура:
├── api/                         # API-маршруты
├── core/                        # Конфигурация и ядро
├── tools/                       # Инструменты: векторизация, графы, NER и др.
├── llm/                         # Обёртки и маршрутизаторы LLM
├── providers/                  # Поставщики моделей LLM
├── .env                         # Конфигурация провайдеров
├── librarian_ai.py              # 🧠 Главный модуль запуска (этот файл)
"""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Абсолютные импорты по архитектуре
from api.files import router as file_router
from api.email import router as email_router
from api.routers.summary import router as summary_router
from api.routers.docs import router as docs_router
from core.config import settings
from core.advanced_architecture import AdvancedApplication

# Создание экземпляра приложения (FastAPI + Telegram через адаптер)
app_instance = AdvancedApplication()
app: FastAPI = app_instance.rest_adapter.app
app.title = "Libra Document Processor"

# Middleware: разрешаем все источники (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роуты API
app.include_router(file_router, prefix="/files", tags=["📁 Files"])
app.include_router(email_router, prefix="/email", tags=["📨 Email"])
app.include_router(summary_router, prefix="/summary", tags=["📄 Summaries"])
app.include_router(docs_router, prefix="/documents", tags=["📚 Documents"])

# Главная страница
@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в Libra Document Processor 🎓",
        "docs": "/docs",
        "files_upload": "/files/upload/",
        "summary": "/summary",
        "documents": "/documents",
        "email_upload": "/email/upload/"
    }

# Проверка статуса
@app.get("/healthz")
def health_check():
    return {"status": "ok", "service": "Libra", "version": settings.VERSION}

# Точка запуска
if __name__ == "__main__":
    asyncio.run(app_instance.start())
