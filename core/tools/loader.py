# 📄 core/tools/loader.py
# 📌 Назначение: Оптимизированная загрузка и обработка файлов

import os
import asyncio
import logging
from typing import List, Tuple, Optional, Dict, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import magic
from dataclasses import dataclass
from datetime import datetime
import hashlib

from utils.file_utils import (
    extract_text_from_pdf, extract_text_from_docx, extract_text_from_xlsx,
    extract_text_from_pptx, extract_text_from_odf, extract_text_from_html,
    extract_text_from_txt, extract_text_from_image
)
from core.tools.archive_extractors import extract_text_from_archive 

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
CACHE_LIMIT = 100
CHUNK_SIZE_DEFAULT = 1000

@dataclass
class FileMetadata:
    name: str
    size: int
    modified: float
    mime_type: str
    checksum: str
    language: str = "en"

@dataclass
class ProcessingResult:
    chunks: List[str]
    metadata: FileMetadata
    processing_time: float

SUPPORTED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.oasis.opendocument.text': 'odt',
    'text/html': 'html',
    'text/plain': 'txt',
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'application/zip': 'zip',
    'application/x-tar': 'tar',
    'application/x-rar-compressed': 'rar'
}

def calculate_checksum(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

class FileProcessingError(Exception):
    pass

class FileLoader:
    def __init__(self, chunker: 'TextChunker', max_workers: int = 4):
        self.chunker = chunker
        self.max_workers = max_workers
        self._cache: Dict[str, ProcessingResult] = {}
        self._cache_hits = 0

    async def load_file(self, file_path: Union[str, Path], chunk_size: int = CHUNK_SIZE_DEFAULT, max_chunks: Optional[int] = None, language: str = "en") -> ProcessingResult:
        file_path = str(file_path)
        if file_path in self._cache:
            self._cache_hits += 1
            return self._cache[file_path]

        if not self._validate_file(file_path):
            raise FileProcessingError(f"Invalid file: {file_path}")

        start_time = datetime.now().timestamp()
        metadata = await self._get_file_metadata(file_path)

        try:
            text = await self._extract_text(file_path, metadata.mime_type)
            chunks = self.chunker.chunk(text, chunk_size, language)
            if max_chunks and len(chunks) > max_chunks:
                chunks = chunks[:max_chunks]
                logger.warning(f"Truncated to {max_chunks} chunks for {file_path}")

            result = ProcessingResult(chunks=chunks, metadata=metadata, processing_time=datetime.now().timestamp() - start_time)
            self._cache[file_path] = result
            self.clear_least_used_cache()
            return result
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
            raise FileProcessingError(f"Failed to process {file_path}") from e

    async def load_files(self, file_paths: List[Union[str, Path]], chunk_size: int = CHUNK_SIZE_DEFAULT, max_workers: Optional[int] = None, timeout: int = 300) -> List[ProcessingResult]:
        results = []
        max_workers = max_workers or self.max_workers

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(executor, lambda p=path: asyncio.run(self.load_file(p, chunk_size)))
                for path in file_paths
            ]
            for future in as_completed(futures, timeout=timeout):
                try:
                    results.append(await future)
                except Exception as e:
                    logger.error(f"File processing failed: {str(e)}")
                    continue
        return results

    async def _extract_text(self, file_path: str, mime_type: str) -> str:
        file_type = SUPPORTED_MIME_TYPES.get(mime_type)
        if not file_type:
            raise ValueError(f"Unsupported file type: {mime_type}")

        extractors = {
            'pdf': extract_text_from_pdf,
            'docx': extract_text_from_docx,
            'pptx': extract_text_from_pptx,
            'xlsx': extract_text_from_xlsx,
            'odt': extract_text_from_odf,
            'html': extract_text_from_html,
            'txt': extract_text_from_txt,
            'jpg': extract_text_from_image,
            'png': extract_text_from_image,
            'zip': extract_text_from_archive,
            'rar': extract_text_from_archive,
            'tar': extract_text_from_archive
        }

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: extractors[file_type](file_path))

    async def _get_file_metadata(self, file_path: str) -> FileMetadata:
        path = Path(file_path)
        mime_type, file_type = detect_file_type(file_path)
        return FileMetadata(
            name=path.name,
            size=path.stat().st_size,
            modified=path.stat().st_mtime,
            mime_type=mime_type,
            checksum=calculate_checksum(file_path),
            language=self._detect_language(file_path)
        )

    def _validate_file(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            return all([
                path.exists(),
                path.is_file(),
                path.stat().st_size <= MAX_FILE_SIZE,
                detect_file_type(file_path)[1] != 'unknown'
            ])
        except Exception:
            return False

    def _detect_language(self, file_path: str) -> str:
        return "en"

    def clear_least_used_cache(self):
        if len(self._cache) > CACHE_LIMIT:
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k].processing_time, reverse=False)
            least_used_key = sorted_keys[0]
            del self._cache[least_used_key]

    def clear_cache(self):
        self._cache.clear()
        self._cache_hits = 0

    @property
    def cache_info(self) -> Dict[str, int]:
        return {
            'cache_size': len(self._cache),
            'cache_hits': self._cache_hits
        }

def detect_file_type(file_path: str) -> Tuple[str, str]:
    mime = magic.from_file(file_path, mime=True)
    return mime, SUPPORTED_MIME_TYPES.get(mime, 'unknown')

def create_file_loader(chunker: 'TextChunker', max_workers: int = 4) -> FileLoader:
    return FileLoader(chunker, max_workers)

from core.parser.chunker import TextChunker

async def load_documents(paths: List[str]) -> List[ProcessingResult]:
    chunker = TextChunker()
    loader = create_file_loader(chunker)
    return await loader.load_files(paths)
