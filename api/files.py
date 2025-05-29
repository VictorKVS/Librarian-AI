# 📄 Файл: files.py
# 📂 Путь: api/
# 📌 Назначение: API эндпоинты для загрузки и обработки файлов через FastAPI

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import tempfile
import shutil

from core.tools.loader import load_file_to_knowledge, parallel_load_files

router = APIRouter()

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        shutil.copyfileobj(file.file, tmpfile)
        tmp_path = tmpfile.name

    try:
        result = load_file_to_knowledge(tmp_path)
        return {"message": f"{len(result)} chunks saved", "filename": file.filename}
    finally:
        os.unlink(tmp_path)


@router.post("/upload/batch/")
async def upload_batch(files: List[UploadFile] = File(...)):
    file_paths = []
    tmp_dir = tempfile.mkdtemp()

    try:
        for file in files:
            tmp_path = os.path.join(tmp_dir, file.filename)
            with open(tmp_path, "wb") as f:
                f.write(await file.read())
            file_paths.append(tmp_path)

        results = parallel_load_files(file_paths)
        return {"files": len(files), "chunks_total": sum(len(r) for r in results)}
    finally:
        shutil.rmtree(tmp_dir)