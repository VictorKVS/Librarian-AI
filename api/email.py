# 📄 Файл: email.py
# 📂 Путь: api/
# 📌 Назначение: Обработка e-mail файлов через POST /email/upload/ (заглушка)

from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/email", tags=["Email"])

@router.post("/upload/")
async def upload_email_file(file: UploadFile = File(...)):
    # В будущем: определить тип, вызвать нужный парсер
    return {
        "filename": file.filename,
        "status": "Заглушка принята",
        "message": "Email-файл получен, обработка будет добавлена."
    }