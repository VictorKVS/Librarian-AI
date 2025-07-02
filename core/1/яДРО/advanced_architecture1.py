# core/advanced_architecture.py
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict

import uvicorn
from fastapi import FastAPI
from pydantic import Field, validator
from injector import inject

# Импорты из пакета librarian_ai
from librarian_ai.core.parser.chunker import TextChunker
from librarian_ai.core.tools.embedder import Embedder
from librarian_ai.core.processor.document_processor import DocumentProcessor, ProcessingConfig, ProcessingResult
from librarian_ai.core.adapters.telegram_adapter import TelegramAdapter, FileType
from librarian_ai.core.application import Application
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict

import uvicorn
from fastapi import FastAPI
from pydantic import Field, validator
from injector import inject

from .parser.chunker import TextChunker
from .tools.embedder import Embedder
from .processor.document_processor import DocumentProcessor, ProcessingConfig, ProcessingResult
from .adapters.telegram_adapter import TelegramAdapter, FileType
from .application import Application

class AdvancedProcessingConfig(ProcessingConfig):
    optimize_for: str = Field("quality", description="Оптимизация: quality, speed или balance")
    enable_analysis: bool = Field(True, description="Включить углубленный анализ")

    @validator('optimize_for')
    def validate_optimization(cls, v):
        modes = {"quality", "speed", "balance"}
        if v not in modes:
            raise ValueError(f"Invalid optimization mode: {v}")
        return v


class AdvancedTextChunker(TextChunker):
    def __init__(self):
        super().__init__()
        self.semaphore = asyncio.Semaphore(10)

    async def chunk(self, text: str, chunk_size: int, language: str) -> List[str]:
        async with self.semaphore:
            # семантическая сегментация (можно расширить)
            return await super().chunk(text, chunk_size, language)


class BatchEmbedder(Embedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(model_name)
        self.batch_size = 32

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            results.extend(await self.generate(batch))
        return results


class AdvancedDocumentProcessor(DocumentProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache: Dict[str, ProcessingResult] = {}

    @asynccontextmanager
    async def processing_session(self, config: AdvancedProcessingConfig) -> AsyncGenerator[str, None]:
        session_id = str(uuid.uuid4())
        try:
            yield session_id
        finally:
            self._cleanup_session(session_id)

    def _cleanup_session(self, session_id: str) -> None:
        # удаляем закешированные результаты сессии
        self.cache.pop(session_id, None)

    async def advanced_process(self, content: str, config: AdvancedProcessingConfig) -> ProcessingResult:
        async with self.processing_session(config) as session_id:
            if config.enable_analysis:
                result = await self._analyze_content(content, config, session_id)
            else:
                result = await super().process(content, config)
            self.cache[session_id] = result
            return result


class AdvancedTelegramAdapter(TelegramAdapter):
    SUPPORTED_TYPES = {FileType.TXT, FileType.PDF}

    async def handle_advanced_message(self, message: Dict) -> Dict:
        if message.get("file_type") not in self.SUPPORTED_TYPES:
            return {"error": "Unsupported file type"}
        return await super().handle_message(message)


class RESTAdapter:
    @inject
    def __init__(self, processor: AdvancedDocumentProcessor):
        self.processor = processor
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.post("/v2/process")
        async def process_endpoint(
            payload: Dict,
            optimize_for: str = "quality",
            enable_analysis: bool = True,
        ) -> ProcessingResult:
            config = AdvancedProcessingConfig(
                optimize_for=optimize_for,
                enable_analysis=enable_analysis,
            )
            return await self.processor.advanced_process(
                payload.get("content", ""), config
            )


class AdvancedApplication(Application):
    def __init__(self):
        super().__init__()
        self.rest_adapter: RESTAdapter = self.injector.get(RESTAdapter)
        self.advanced_processor: AdvancedDocumentProcessor = self.injector.get(AdvancedDocumentProcessor)
        self.telegram_adapter: TelegramAdapter = self.injector.get(TelegramAdapter)
        self.app: FastAPI = self.rest_adapter.app

    async def start(self) -> None:
        rest_task = asyncio.create_task(self._start_rest())
        telegram_task = asyncio.create_task(self._start_telegram())
        await asyncio.gather(rest_task, telegram_task)

    async def _start_telegram(self) -> None:
        # делегируем старт адаптеру
        await self.telegram_adapter.start()

    async def _start_rest(self) -> None:
        config = uvicorn.Config(self.app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()


class ContentAnalyzer:
    @inject
    def __init__(self, embedder: Embedder):
        self.embedder = embedder

    async def analyze_sentiment(self, text: str) -> Dict:
        embedding = await self.embedder.generate([text])
        score = sum(embedding[0])
        return {"sentiment": "positive" if score > 0 else "negative"}


class ClusterManager:
    def __init__(self):
        self.nodes: List[DocumentProcessor] = []

    async def add_node(self, processor: DocumentProcessor) -> None:
        self.nodes.append(processor)


# Пример запуска
async def advanced_main() -> None:
    app = AdvancedApplication()
    await app.start()


if __name__ == "__main__":
    asyncio.run(advanced_main())
