import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.files import router as file_router
from app.api.email import router as email_router
from app.api.routers.summary import router as summary_router
from app.api.routers.docs import router as docs_router
from app.core.config import settings
from app.core.advanced_architecture import AdvancedApplication

# Создание экземпляра приложения, включающего FastAPI и Telegram
app_instance = AdvancedApplication()
app = app_instance.rest_adapter.app  # FastAPI instance
app.title = "Libra Document Processor"

# Разрешаем CORS с любых источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты
app.include_router(file_router, prefix="/files", tags=["📁 Files"])
app.include_router(email_router, prefix="/email", tags=["📨 Email"])
app.include_router(summary_router, prefix="/summary", tags=["📄 Summaries"])
app.include_router(docs_router, prefix="/documents", tags=["documents"])

# Базовый endpoint
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

# Health check
@app.get("/healthz")
def health_check():
    return {"status": "ok", "service": "Libra", "version": settings.VERSION}

# Запуск приложения (FastAPI + Telegram)
if __name__ == "__main__":
    asyncio.run(app_instance.start())