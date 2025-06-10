# 📄 Файл: documents.py | Расположение: librarian_ai/api/documents.py
# 📌 Назначение: REST API для загрузки, обработки и векторизации документов
# 📥 Получает: файл или путь к файлу
# 📤 Передаёт: статус, результат векторизации, ID документа в базе

from fastapi import APIRouter, UploadFile, File
from librarian_ai.core.loader import load_documents
from librarian_ai.core.parser import parse_text_file
from librarian_ai.core.embedder import Embedder
from librarian_ai.core.storage import save_to_db
import os

router = APIRouter()
embedder = Embedder()

@router.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    temp_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    parsed = parse_text_file(temp_path)
    if "text" not in parsed:
        return {"error": parsed.get("error", "Ошибка при парсинге")}

    chunks = [parsed["text"][i:i+3000] for i in range(0, len(parsed["text"]), 3000)]
    vectors = embedder.encode(chunks)
    meta = [{"filename": parsed["meta"]["filename"], "chunk": i} for i in range(len(chunks))]

    embedder.save_index(vectors, meta)
    save_to_db(parsed["text"], parsed["meta"])

    os.remove(temp_path)
    return {"status": "ok", "chunks": len(chunks), "filename": parsed["meta"]["filename"]}
