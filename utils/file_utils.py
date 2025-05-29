# 📄 Файл: file_utils.py
# 📂 Путь: utils/
# 📌 Назначение: Оптимизированное извлечение текста из файлов с поддержкой асинхронности и кеширования

import os
import io
import logging
import asyncio
import aiofiles
from typing import Optional, Dict, Callable, List, Tuple, AsyncGenerator
from functools import lru_cache, partial
from pathlib import Path
import mimetypes
from enum import Enum, auto
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import tempfile

logger = logging.getLogger(__name__)

# Инициализация MIME-типов
mimetypes.init()
mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')
mimetypes.add_type('application/vnd.oasis.opendocument.text', '.odt')

# Константы
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 4096  # Для потокового чтения

class FileType(Enum):
    PDF = auto()
    DOCX = auto()
    XLSX = auto()
    PPTX = auto()
    HTML = auto()
    TEXT = auto()
    ODT = auto()
    IMAGE = auto()
    UNSUPPORTED = auto()

@dataclass
class FileMetadata:
    size: int
    mime_type: str
    modified: float

# 🔄 Асинхронные версии функций
async def extract_text_from_pdf_async(path: str) -> str:
    from pdfminer.high_level import extract_text
    async with aiofiles.open(path, 'rb') as f:
        data = await f.read()
        return extract_text(io.BytesIO(data))

async def extract_text_from_docx_async(path: str) -> str:
    from docx import Document
    async with aiofiles.open(path, 'rb') as f:
        doc = Document(io.BytesIO(await f.read()))
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

# ... аналогичные асинхронные версии для других форматов ...

class FileProcessor:
    """Усовершенствованный процессор файлов с поддержкой асинхронности"""
    
    def __init__(self):
        self._sync_handlers = {
            FileType.PDF: extract_text_from_pdf,
            FileType.DOCX: extract_text_from_docx,
            # ... другие синхронные обработчики
        }
        self._async_handlers = {
            FileType.PDF: extract_text_from_pdf_async,
            FileType.DOCX: extract_text_from_docx_async,
            # ... другие асинхронные обработчики
        }
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def get_metadata(self, path: str) -> FileMetadata:
        """Асинхронно получает метаданные файла"""
        stat = await aiofiles.os.stat(path)
        mime_type, _ = mimetypes.guess_type(path)
        return FileMetadata(
            size=stat.st_size,
            mime_type=mime_type or 'application/octet-stream',
            modified=stat.st_mtime
        )

    async def process_async(self, path: str) -> str:
        """Асинхронная обработка файла"""
        file_type = get_file_type(path)
        handler = self._async_handlers.get(file_type)
        if not handler:
            raise ValueError(f"Unsupported file type: {file_type}")
        return await handler(path)

    def process(self, path: str) -> str:
        """Синхронная обработка файла"""
        file_type = get_file_type(path)
        handler = self._sync_handlers.get(file_type)
        if not handler:
            raise ValueError(f"Unsupported file type: {file_type}")
        return handler(path)

    async def stream_file(self, path: str) -> AsyncGenerator[str, None]:
        """Потоковая передача содержимого файла"""
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            while chunk := await f.read(CHUNK_SIZE):
                yield chunk

    async def process_large_file(self, path: str) -> str:
        """Обработка больших файлов с потоковым чтением"""
        content = []
        async for chunk in self.stream_file(path):
            content.append(chunk)
        return ''.join(content)

    async def extract_to_temp(self, path: str) -> Tuple[str, str]:
        """Извлекает текст во временный файл"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp:
            content = await self.process_async(path)
            tmp.write(content)
            return tmp.name, content

# 🧠 Улучшенное определение типа файла
@lru_cache(maxsize=1000)
def get_file_type(path: str) -> FileType:
    """Определяет тип файла с кешированием"""
    try:
        mime_type, _ = mimetypes.guess_type(path)
        ext = Path(path).suffix.lower()

        if mime_type:
            if "pdf" in mime_type:
                return FileType.PDF
            elif "wordprocessingml" in mime_type:
                return FileType.DOCX
            elif "presentationml" in mime_type:
                return FileType.PPTX
            elif "spreadsheetml" in mime_type:
                return FileType.XLSX
            elif "text/html" in mime_type:
                return FileType.HTML
            elif "text/plain" in mime_type:
                return FileType.TEXT
            elif "opendocument.text" in mime_type:
                return FileType.ODT
            elif "image" in mime_type:
                return FileType.IMAGE

        return {
            '.pdf': FileType.PDF,
            '.docx': FileType.DOCX,
            '.pptx': FileType.PPTX,
            '.xlsx': FileType.XLSX,
            '.odt': FileType.ODT,
            '.txt': FileType.TEXT,
            '.html': FileType.HTML,
            '.htm': FileType.HTML,
            '.jpg': FileType.IMAGE,
            '.jpeg': FileType.IMAGE,
            '.png': FileType.IMAGE,
        }.get(ext, FileType.UNSUPPORTED)
    except Exception as e:
        logger.error(f"Failed to determine file type for {path}: {str(e)}")
        return FileType.UNSUPPORTED

# 🧩 Универсальные интерфейсы
file_processor = FileProcessor()

async def extract_text_async(path: str) -> str:
    """Асинхронный интерфейс для извлечения текста"""
    return await file_processor.process_async(path)

def extract_text(path: str) -> str:
    """Синхронный интерфейс для извлечения текста"""
    return file_processor.process(path)

async def process_batch_async(paths: List[str]) -> Dict[str, str]:
    """Асинхронная пакетная обработка"""
    tasks = [extract_text_async(path) for path in paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {path: result for path, result in zip(paths, results) if not isinstance(result, Exception)}

def process_batch(paths: List[str]) -> Dict[str, str]:
    """Синхронная пакетная обработка"""
    with ThreadPoolExecutor() as executor:
        return dict(zip(paths, executor.map(extract_text, paths)))

# Пример использования
async def example_usage():
    # Одиночная обработка
    text = await extract_text_async("document.docx")
    print(f"Extracted text length: {len(text)}")
    
    # Пакетная обработка
    results = await process_batch_async(["file1.pdf", "file2.docx"])
    for path, content in results.items():
        print(f"{path}: {content[:100]}...")

if __name__ == "__main__":
    asyncio.run(example_usage())