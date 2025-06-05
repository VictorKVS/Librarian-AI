# core/advanced_architecture.py

import logging
import sqlite3
import json

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from threading import Thread
import importlib

from dependency_injector import containers, providers
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# --- Конфигурация ---
from config.secrets import Settings

# --- Безопасность / Auth ---
from core.core_auth.jwt_handler import create_token, verify_token
# Импортируем oauth2_scheme и get_current_user
from core.core_auth.oauth2 import oauth2_scheme as OAuth2Scheme, get_current_user

# --- Модели данных ---
from core.models.database import Database
from core.models.schemas import UserSchema, DocumentSchema

# --- Парсеры / Предобработка ---
from core.parser.loader import FileLoader
from core.parser.chunker import SmartChunker
from core.parser.parser import MultilingualParser

# --- RAG-компоненты ---
from core.rag.retriever import HybridRetriever
from core.rag.processor import DocumentProcessor
from core.rag.librarian import LibrarianAI

# --- Сервисы ---
from core.services.embedding import EmbeddingService
from core.services.search import SemanticSearch
from core.services.summary import SummaryService
from core.services.ner import NERService
from core.services.knowledge_graph import KnowledgeGraph
from core.services.tasks import TaskManager

# --- Полнотекстовый поиск (SQLite FTS5) ---
from core.services.keyword_search import KeywordSearch

# --- Адаптеры (опциональные) ---
try:
    from core.adapters.telegram import TelegramBot
    from core.adapters.web import WebInterface
    from core.adapters.erp import ERPIntegration
except ImportError:
    TelegramBot = None
    WebInterface = None
    ERPIntegration = None

# Логгер для ядра
logger = logging.getLogger("librarian_core")
logging.basicConfig(level=logging.INFO)


@dataclass
class KeywordSearchResult:
    doc_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = None


class CoreContainer(containers.DeclarativeContainer):
    """
    Контейнер зависимостей для ядра Librarian AI.
    Собираем все сервисы, RAG-компоненты и адаптеры в одном месте.
    """

    # --- Конфигурация ---
    config = providers.Singleton(Settings)

    # --- База данных ---
    database = providers.Singleton(
        Database,
        dsn=(
            config.provided.DB_TYPE
            + "://"
            + config.provided.DB_USER
            + ":"
            + config.provided.DB_PASSWORD
            + "@"
            + config.provided.DB_HOST
            + ":"
            + str(config.provided.DB_PORT)
            + "/"
            + config.provided.DB_NAME
        ),
        pool_size=config.provided.DB_POOL_SIZE,
        max_overflow=config.provided.DB_MAX_OVERFLOW,
        timeout=config.provided.DB_TIMEOUT,
        pool_recycle=3600,
        echo=(config.provided.DEBUG if hasattr(config.provided, "DEBUG") else False),
    )

    # --- Безопасность / Auth ---
    jwt_functions = providers.Object({"create": create_token, "verify": verify_token})
    auth_scheme = providers.Singleton(OAuth2Scheme)

    # --- Парсеры / Предобработка ---
    file_loader = providers.Factory(
        FileLoader,
        max_file_size=config.provided.MAX_FILE_SIZE,
    )
    chunker = providers.Factory(
        SmartChunker,
        chunk_size=config.provided.CHUNK_SIZE if hasattr(config.provided, "CHUNK_SIZE") else 1000,
        overlap=config.provided.CHUNK_OVERLAP if hasattr(config.provided, "CHUNK_OVERLAP") else 100,
    )
    text_parser = providers.Factory(
        MultilingualParser,
        languages=config.provided.ALLOWED_EXTENSIONS if hasattr(config.provided, "ALLOWED_EXTENSIONS") else ["ru", "en"],
    )

    # --- Сервисы ---
    embedding_service = providers.Singleton(
        EmbeddingService,
        model_name=config.provided.LLM_PROVIDER,
        device="cpu",
    )
    search_service = providers.Singleton(
        SemanticSearch,
        embedder=embedding_service,
        index_config=config.provided.paths["vector_store"] if hasattr(config.provided, "paths") else "knowledge/vector_store/",
    )
    summary_service = providers.Singleton(
        SummaryService,
        model_name=config.provided.MISTRAL_MODEL_PATH if hasattr(config.provided, "MISTRAL_MODEL_PATH") else None,
    )
    ner_service = providers.Singleton(
        NERService,
        models=config.provided.ner_models if hasattr(config.provided, "ner_models") else ["spacy-en", "natasha-ru"],
    )
    knowledge_graph = providers.Singleton(
        KnowledgeGraph,
        db=database,
    )
    task_manager = providers.Singleton(
        TaskManager,
        broker_url=config.provided.CELERY_BROKER_URL,
        result_backend=config.provided.CELERY_RESULT_BACKEND,
    )

    # --- Полнотекстовый поиск (KeywordSearch) ---
    keyword_search = providers.Singleton(
        KeywordSearch,
        index_path=(
            config.provided.paths["vector_store"] + "keyword_index.db"
            if hasattr(config.provided, "paths")
            else "knowledge/keyword_index.db"
        ),
        enable_highlighting=True,
    )

    # --- RAG-компоненты ---
    retriever = providers.Singleton(
        HybridRetriever,
        vector_search=search_service,
        keyword_search=keyword_search,
    )
    doc_processor = providers.Factory(
        DocumentProcessor,
        chunker=chunker,
        embedder=embedding_service,
        parser=text_parser,
    )
    librarian = providers.Singleton(
        LibrarianAI,
        retriever=retriever,
        processor=doc_processor,
        ner=ner_service,
        graph=knowledge_graph,
    )

    # --- Адаптеры ---
    telegram_bot = (
        providers.Singleton(
            TelegramBot,
            token=config.provided.paths["logs"] if hasattr(config.provided, "paths") else "",
            service=librarian,
        )
        if TelegramBot
        else None
    )
    web_interface = (
        providers.Singleton(
            WebInterface,
            host=config.provided.web["host"]
            if hasattr(config.provided, "web") and "host" in config.provided.web
            else "0.0.0.0",
            port=config.provided.web["port"]
            if hasattr(config.provided, "web") and "port" in config.provided.web
            else 8001,
            service=librarian,
        )
        if WebInterface
        else None
    )
    erp_integration = (
        providers.Singleton(
            ERPIntegration,
            connection=config.provided.erp["connection_string"]
            if hasattr(config.provided, "erp") and "connection_string" in config.provided.erp
            else "",
            service=librarian,
        )
        if ERPIntegration
        else None
    )


def create_app() -> FastAPI:
    """
    Фабрика FastAPI-приложения:
      1. Инициализирует DI-контейнер (CoreContainer) и настраивает логирование.
      2. Регистрирует middleware (CORS), роутеры и зависимости по auth.
      3. Запускает адаптеры (Telegram, Web, ERP) в отдельном потоке.
      4. Возвращает готовое приложение.
    """
    container = CoreContainer()
    config = container.config()

    logging.getLogger().setLevel(config.provided.LOG_LEVEL if hasattr(config.provided, "LOG_LEVEL") else "INFO")

    app = FastAPI(
        title=config.provided.name if hasattr(config.provided, "name") else "Librarian AI",
        version=config.provided.VERSION if hasattr(config.provided, "VERSION") else "1.0.0",
        docs_url="/docs" if getattr(config.provided, "enable_docs", True) else None,
    )
    app.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(config.provided, "cors_origins", ["*"]),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    routers = [
        ("auth", "/auth", ["auth"]),
        ("search", "/search", ["search"]),
        ("summary", "/summaries", ["summarization"]),
        ("files", "/files", ["files"]),
        ("processing", "/process", ["processing"]),
        ("status", "/status", ["monitoring"]),
        ("email", "/email", ["email"]),
    ]

    for module, prefix, tags in routers:
        try:
            router = importlib.import_module(f"api.{module}").router
            if module in ("auth", "email"):
                app.include_router(router, prefix=prefix, tags=tags)
            else:
                app.include_router(
                    router,
                    prefix=prefix,
                    dependencies=[Depends(get_current_user)],
                    tags=tags,
                )
        except ImportError as e:
            container.logger().warning(f"Router {module} not loaded: {str(e)}")

    def start_adapters():
        adapters = [
            container.telegram_bot,
            container.web_interface,
            container.erp_integration,
        ]
        for adapter in filter(None, adapters):
            try:
                adapter().start()
                container.logger().info(f"Started adapter: {adapter}")
            except Exception as e:
                container.logger().error(f"Adapter failed: {str(e)}")

    Thread(target=start_adapters, daemon=True).start()

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "OK", "version": config.provided.VERSION}

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(
        "core.advanced_architecture:create_app",
        host="0.0.0.0",
        port=8000,
        reload=getattr(app.container.config().provided, "debug", True),
        log_level="info",
    )
