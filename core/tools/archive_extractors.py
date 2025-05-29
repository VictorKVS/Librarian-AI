# 📄 Файл: core/tools/archive_extractors.py
# 📌 Назначение: Извлечение текста из архивов с поддержкой асинхронности и парольной защиты

import os
import io
import zipfile
import tarfile
import rarfile
import logging
from typing import List, Dict, Tuple, Optional, AsyncIterator
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum, auto
import tempfile
import aiofiles
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ArchiveType(Enum):
    ZIP = auto()
    TAR = auto()
    RAR = auto()
    SEVENZIP = auto()  # Будущая поддержка 7-zip

@dataclass
class ArchiveContent:
    text: str
    files: List[str]
    metadata: Dict[str, str]
    warnings: List[str]

# Поддерживаемые текстовые расширения
TEXT_EXTENSIONS = {
    '.txt', '.md', '.csv',
    '.html', '.htm', '.xml',
    '.pdf', '.docx', '.pptx', '.xlsx',
    '.odt', '.rtf', '.json'
}

# Безопасные лимиты для избежания атаки DOS
MAX_EXTRACT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILES = 1000

class ArchiveError(Exception):
    """Исключение для ошибок обработки архивов"""
    pass

async def _stream_read(file_obj, max_size: int) -> AsyncIterator[str]:
    """Потоковое чтение файла с лимитом размера"""
    buffer = b""
    async for chunk in file_obj:
        buffer += chunk
        if len(buffer) > max_size:
            break
        yield buffer.decode('utf-8', errors='replace')

def _is_text_file(filename: str) -> bool:
    """Проверяет, является ли файл текстовым по расширению"""
    return Path(filename).suffix.lower() in TEXT_EXTENSIONS

@lru_cache(maxsize=100)
def detect_archive_type(path: str) -> ArchiveType:
    """Определение типа архива с кешированием"""
    ext = Path(path).suffix.lower()
    mapping = {
        '.zip': ArchiveType.ZIP,
        '.tar': ArchiveType.TAR,
        '.rar': ArchiveType.RAR,
        '.7z': ArchiveType.SEVENZIP
    }
    if ext not in mapping:
        raise ArchiveError(f"Unsupported archive format: {ext}")
    return mapping[ext]

@asynccontextmanager
async def _async_zip_reader(path: str):
    """Асинхронный контекстный менеджер для ZIP"""
    async with aiofiles.open(path, 'rb') as f:
        data = await f.read()
    yield zipfile.ZipFile(io.BytesIO(data))

@asynccontextmanager
async def _async_tar_reader(path: str):
    """Асинхронный контекстный менеджер для TAR"""
    async with aiofiles.open(path, 'rb') as f:
        data = await f.read()
    yield tarfile.open(fileobj=io.BytesIO(data), mode='r:*')

async def extract_from_zip(path: str) -> ArchiveContent:
    """Асинхронное извлечение из ZIP с потоковой обработкой"""
    warnings = []
    contents = []
    files_list = []
    total_size = 0
    
    try:
        async with _async_zip_reader(path) as archive:
            for file_info in archive.infolist():
                if len(files_list) >= MAX_FILES:
                    warnings.append(f"Maximum number of files exceeded ({MAX_FILES})")
                    break
                
                if file_info.is_dir() or not _is_text_file(file_info.filename):
                    continue
                
                if file_info.file_size > MAX_EXTRACT_SIZE:
                    warnings.append(f"File {file_info.filename} too large ({file_info.file_size} bytes)")
                    continue
                
                total_size += file_info.file_size
                if total_size > MAX_TOTAL_SIZE:
                    warnings.append(f"Total size limit exceeded ({MAX_TOTAL_SIZE} bytes)")
                    break
                
                try:
                    with archive.open(file_info) as file_obj:
                        content = []
                        async for chunk in _stream_read(file_obj, MAX_EXTRACT_SIZE):
                            content.append(chunk)
                        if content:
                            contents.append("".join(content))
                            files_list.append(file_info.filename)
                except Exception as e:
                    warnings.append(f"Error extracting {file_info.filename}: {str(e)}")
        
        return ArchiveContent(
            text="\n\n".join(contents),
            files=files_list,
            metadata={'format': 'ZIP'},
            warnings=warnings
        )
    except Exception as e:
        logger.error(f"ZIP extraction failed: {str(e)}")
        raise ArchiveError(f"ZIP processing error: {str(e)}") from e

async def extract_from_tar(path: str) -> ArchiveContent:
    """Асинхронное извлечение из TAR с потоковой обработкой"""
    warnings = []
    contents = []
    files_list = []
    total_size = 0
    
    try:
        async with _async_tar_reader(path) as archive:
            for member in archive.getmembers():
                if len(files_list) >= MAX_FILES:
                    warnings.append(f"Maximum number of files exceeded ({MAX_FILES})")
                    break
                
                if not member.isfile() or not _is_text_file(member.name):
                    continue
                
                if member.size > MAX_EXTRACT_SIZE:
                    warnings.append(f"File {member.name} too large ({member.size} bytes)")
                    continue
                
                total_size += member.size
                if total_size > MAX_TOTAL_SIZE:
                    warnings.append(f"Total size limit exceeded ({MAX_TOTAL_SIZE} bytes)")
                    break
                
                try:
                    file_obj = archive.extractfile(member)
                    if file_obj:
                        content = []
                        async for chunk in _stream_read(file_obj, MAX_EXTRACT_SIZE):
                            content.append(chunk)
                        if content:
                            contents.append("".join(content))
                            files_list.append(member.name)
                except Exception as e:
                    warnings.append(f"Error extracting {member.name}: {str(e)}")
        
        return ArchiveContent(
            text="\n\n".join(contents),
            files=files_list,
            metadata={'format': 'TAR'},
            warnings=warnings
        )
    except Exception as e:
        logger.error(f"TAR extraction failed: {str(e)}")
        raise ArchiveError(f"TAR processing error: {str(e)}") from e

class ArchiveExtractor:
    """Интерфейс для работы с архивами"""
    
    def __init__(self):
        self._handlers = {
            ArchiveType.ZIP: extract_from_zip,
            ArchiveType.TAR: extract_from_tar,
            ArchiveType.RAR: extract_from_rar,
        }
    
    async def extract(self, path: str) -> ArchiveContent:
        """Основной метод извлечения содержимого"""
        try:
            archive_type = detect_archive_type(path)
            handler = self._handlers.get(archive_type)
            if not handler:
                raise ArchiveError(f"No handler for {archive_type}")
            
            return await handler(path)
        except Exception as e:
            logger.error(f"Archive processing failed: {str(e)}")
            raise ArchiveError(f"Failed to process archive: {str(e)}") from e

    async def extract_files(self, path: str) -> AsyncIterator[Tuple[str, str]]:
        """Потоковая выдача файлов из архива"""
        archive_type = detect_archive_type(path)
        
        if archive_type == ArchiveType.ZIP:
            async with _async_zip_reader(path) as archive:
                for file_info in archive.infolist():
                    if not file_info.is_dir() and _is_text_file(file_info.filename):
                        with archive.open(file_info) as file_obj:
                            content = []
                            async for chunk in _stream_read(file_obj, MAX_EXTRACT_SIZE):
                                content.append(chunk)
                            yield file_info.filename, "".join(content)
        
        elif archive_type == ArchiveType.TAR:
            async with _async_tar_reader(path) as archive:
                for member in archive.getmembers():
                    if member.isfile() and _is_text_file(member.name):
                        file_obj = archive.extractfile(member)
                        if file_obj:
                            content = []
                            async for chunk in _stream_read(file_obj, MAX_EXTRACT_SIZE):
                                content.append(chunk)
                            yield member.name, "".join(content)

async def extract_text_from_archive(path: str) -> str:
    """Упрощенный интерфейс для извлечения текста"""
    return (await ArchiveExtractor().extract(path)).text

# Пример использования
async def main():
    # Простое извлечение
    content = await extract_text_from_archive("data.zip")
    print(content)
    
    # Расширенное использование
    extractor = ArchiveExtractor()
    result = await extractor.extract("presentation.tar")
    print(f"Extracted {len(result.files)} files with {len(result.warnings)} warnings")
    
    # Потоковая обработка
    async for filename, text in extractor.extract_files("large_archive.rar"):
        print(f"Processing {filename}...")
        # Обработка каждого файла по мере извлечения

if __name__ == "__main__":
    asyncio.run(main())