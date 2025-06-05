# core/advanced_architecture.py
i# core/advanced_architecture.py

from dependency_injector import containers, providers
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware              # ИМПОРТ
from threading import Thread                                     # ИМПОРТ
import importlib                                                  # ИМПОРТ

# Конфигурация
from config.config import Settings
from config.remote import RemoteConfig

# Безопасность
from core.security.jwt_handler import JWTHandler
from core.security.oauth_scheme import OAuth2Scheme
from core.security.dependencies import get_current_user

# Модели данных
from core.models.database import Database
from core.models.schemas import UserSchema, DocumentSchema

# Обработка документов
from core.parsing.loader import FileLoader
from core.parsing.chunker import SmartChunker
from core.parsing.parser import MultilingualParser

# RAG компоненты
from core.rag.retriever import HybridRetriever
from core.rag.processor import DocumentProcessor
from core.rag.librarian import LibrarianAI

# Сервисы
from core.services.embedding import EmbeddingService
from core.services.search import SemanticSearch
from core.services.summary import SummaryService
from core.services.ner import NERService
from core.services.knowledge_graph import KnowledgeGraph
from core.services.tasks import TaskManager

# Класс для поиска по ключевым словам (надо убедиться, что он действительно у вас есть)
try:
    from core.services.keyword_search import KeywordSearch
except ImportError:
    KeywordSearch = None

# Адаптеры (опциональные)
try:
    from core.adapters.telegram import TelegramBot
    from core.adapters.web import WebInterface
    from core.adapters.erp import ERPIntegration
except ImportError:
    TelegramBot = None
    WebInterface = None
    ERPIntegration = None

class CoreContainer(containers.DeclarativeContainer):
    """Контейнер зависимостей с улучшенной организацией и типизацией"""

    # Конфигурация
    config = providers.Singleton(Settings)
    remote_config = providers.Singleton(RemoteConfig)

    # База данных
    database = providers.Singleton(
        Database,
        dsn=config.provided.database.dsn,
        pool_size=config.provided.database.pool_size,
    )

    # Безопасность
    jwt_handler = providers.Singleton(
        JWTHandler,
        secret=config.provided.security.secret_key,
        algorithm=config.provided.security.algorithm,
        expiry=config.provided.security.token_expiry
    )
    
    auth_scheme = providers.Singleton(
        OAuth2Scheme,
        jwt_handler=jwt_handler
    )

    # Парсеры
    file_loader = providers.Factory(
        FileLoader,
        max_file_size=config.provided.parsing.max_file_size
    )
    
    chunker = providers.Factory(
        SmartChunker,
        chunk_size=config.provided.parsing.chunk_size,
        overlap=config.provided.parsing.chunk_overlap
    )
    
    text_parser = providers.Factory(
        MultilingualParser,
        languages=config.provided.parsing.supported_languages
    )

    # Сервисы
    embedding_service = providers.Singleton(
        EmbeddingService,
        model_name=config.provided.embeddings.model,
        device=config.provided.embeddings.device
    )
    
    search_service = providers.Singleton(
        SemanticSearch,
        embedder=embedding_service,
        index_config=config.provided.search
    )
    
    summary_service = providers.Singleton(
        SummaryService,
        model_name=config.provided.summarization.model
    )
    
    ner_service = providers.Singleton(
        NERService,
        models=config.provided.ner.models
    )
    
    knowledge_graph = providers.Singleton(
        KnowledgeGraph,
        db=database
    )
    
    task_manager = providers.Singleton(
        TaskManager,
        broker_url=config.provided.tasks.broker_url,
        result_backend=config.provided.tasks.result_backend
    )

    # RAG компоненты
    retriever = providers.Singleton(
        HybridRetriever,
        vector_search=search_service,
        keyword_search=(
            providers.Factory(
                KeywordSearch,
                index_name=config.provided.search.keyword_index
            ) if KeywordSearch else None
        )
    )
    
    doc_processor = providers.Factory(
        DocumentProcessor,
        chunker=chunker,
        embedder=embedding_service,
        parser=text_parser
    )
    
    librarian = providers.Singleton(
        LibrarianAI,
        retriever=retriever,
        processor=doc_processor,
        ner=ner_service,
        graph=knowledge_graph
    )

    # Адаптеры (динамическая инициализация)
    telegram_bot = providers.Singleton(
        TelegramBot,
        token=config.provided.telegram.token,
        service=librarian
    ) if TelegramBot else None
    
    web_interface = providers.Singleton(
        WebInterface,
        config=config.provided.web,
        service=librarian
    ) if WebInterface else None
    
    erp_integration = providers.Singleton(
        ERPIntegration,
        connection=config.provided.erp.connection_string,
        service=librarian
    ) if ERPIntegration else None

    # Логгер (если у вас не реализован, можно подключить стандартный logging)
    # Например:
    # import logging
    # logger = providers.Singleton(logging.getLogger, name="core")
    # И потом использовать container.logger().warning(...)

def create_app() -> FastAPI:
    """Фабрика приложения с улучшенной обработкой ошибок"""
    
    # Инициализация контейнера
    container = CoreContainer()
    config = container.config()

    # Настраиваем логгер, если он есть:
    # container.logger().setLevel(config.provided.logging.level)
    
    # Создание FastAPI приложения
    app = FastAPI(
        title=config.app.name,
        version=config.app.version,
        docs_url="/docs" if config.app.enable_docs else None
    )
    
    # Контекст зависимостей (чтобы в роутерах можно было писать Depends(Provide[CoreContainer.xxx]))
    app.container = container
    
    # Регистрация CORS, если нужно
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Динамическая регистрация роутеров
    routers = [
        ("search", "/search", ["search"]),
        ("summary", "/summaries", ["summarization"]),
        ("files", "/files", ["files"]),
        ("processing", "/process", ["processing"]),
        ("status", "/status", ["monitoring"]),
        ("email", "/email", ["email"])           # Добавил роутер для email
    ]
    
    for module, prefix, tags in routers:
        try:
            router = importlib.import_module(f"api.{module}").router
            app.include_router(
                router,
                prefix=prefix,
                dependencies=[Depends(get_current_user)],
                tags=tags
            )
        except ImportError as e:
            # Если logger в контейнере не настроен, замените на print или logging
            try:
                container.logger().warning(f"Router {module} not loaded: {str(e)}")
            except Exception:
                print(f"[WARNING] Router {module} not loaded: {str(e)}")
    
    # Запуск адаптеров в фоне (если они существуют)
    def start_adapters():
        adapters = [
            container.telegram_bot,
            container.web_interface,
            container.erp_integration
        ]
        
        for adapter in filter(None, adapters):
            try:
                adapter().start()
            except Exception as e:
                try:
                    container.logger().error(f"Adapter failed: {str(e)}")
                except Exception:
                    print(f"[ERROR] Adapter failed: {str(e)}")
    
    Thread(target=start_adapters, daemon=True).start()
    
    # Простая эндпоинт для хелсчека
    @app.get("/health")
    async def health_check():
        return {"status": "OK", "version": config.app.version}
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=app.container.config().app.debug,
        log_level="info"
    )
