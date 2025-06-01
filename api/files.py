# 📄 Файл: files.py
# 📂 Путь: api/
# 📌 Назначение: API эндпоинты для загрузки и обработки файлов через FastAPI

# 📄 Файл: api/files.py
# 📌 Назначение: API эндпоинты для загрузки и обработки файлов

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import List
import os
import logging
import aiofiles
import tempfile
import asyncio
from starlette.responses import JSONResponse

from core.tools.loader import create_file_loader
from core.parser.chunker import TextChunker

# from auth.dependencies import get_current_user  # 🔐 Раскомментировать, если используете JWT

logger = logging.getLogger(__name__)
router = APIRouter()

# 🚀 Инициализация загрузчика
chunker = TextChunker()
loader = create_file_loader(chunker)

# 🔒 Ограничения
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'application/zip',
    'application/x-tar',
    'application/x-rar-compressed'
}
MAX_FILE_SIZE_MB = 50


# ✅ Проверка MIME-типа и размера
async def validate_file(file: UploadFile):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Недопустимый MIME-тип: {file.content_type}")

    await file.seek(0, os.SEEK_END)
    size = file.tell()
    if size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Превышен максимальный размер файла: {size // 1024} KB")
    await file.seek(0)


# ✅ Одиночная загрузка и обработка
@router.post("/upload/", status_code=status.HTTP_200_OK)
async def upload_file(file: UploadFile = File(...)):
    await validate_file(file)
    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        async with aiofiles.open(tmp.name, 'wb') as out:
            content = await file.read()
            await out.write(content)
        tmp_path = tmp.name

    try:
        result = await loader.load_file(tmp_path)
        return {
            "filename": file.filename,
            "chunk_count": len(result.chunks),
            "language": result.metadata.language,
            "size_kb": result.metadata.size // 1024,
            "mime_type": result.metadata.mime_type,
            "processing_time": round(result.processing_time, 2),
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки файла")
    finally:
        os.unlink(tmp_path)


# ✅ Пакетная загрузка
@router.post("/upload/batch/", status_code=status.HTTP_200_OK)
async def upload_batch(files: List[UploadFile] = File(...)):
    async def process_one(file: UploadFile):
        await validate_file(file)
        suffix = os.path.splitext(file.filename)[1]

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            async with aiofiles.open(tmp.name, 'wb') as out:
                content = await file.read()
                await out.write(content)
            tmp_path = tmp.name

        try:
            result = await loader.load_file(tmp_path)
            return {
                "filename": file.filename,
                "chunk_count": len(result.chunks),
                "language": result.metadata.language,
                "size_kb": result.metadata.size // 1024,
                "mime_type": result.metadata.mime_type,
                "processing_time": round(result.processing_time, 2),
            }
        except Exception as e:
            logger.error(f"Ошибка обработки файла {file.filename}: {str(e)}", exc_info=True)
            return {
                "filename": file.filename,
                "error": str(e)
            }
        finally:
            os.unlink(tmp_path)

    results = await asyncio.gather(*(process_one(file) for file in files))
    return {
        "files_processed": len(results),
        "details": results
    }


# ✅ Потоковая загрузка больших файлов
@router.post("/upload/stream/", status_code=status.HTTP_200_OK)
async def upload_stream_file(file: UploadFile = File(...)):
    await validate_file(file)
    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        async with aiofiles.open(tmp.name, 'wb') as out:
            while chunk := await file.read(1024 * 1024):  # читаем по 1 МБ
                await out.write(chunk)
        tmp_path = tmp.name

    try:
        result = await loader.load_file(tmp_path)
        return {
            "filename": file.filename,
            "chunk_count": len(result.chunks),
            "language": result.metadata.language,
            "size_kb": result.metadata.size // 1024,
            "mime_type": result.metadata.mime_type,
            "processing_time": round(result.processing_time, 2),
        }
    except Exception as e:
        logger.error(f"Ошибка при потоковой загрузке {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обработки потока")
    finally:
        os.unlink(tmp_path)


# ✅ Проверка совместимости файла
@router.get("/check/{filename}", status_code=status.HTTP_200_OK)
async def check_file_compatibility(filename: str):
    _, ext = os.path.splitext(filename.lower())
    compatible = ext in ['.pdf', '.docx', '.xlsx', '.txt', '.zip', '.tar', '.rar']
    return JSONResponse({"compatible": compatible})