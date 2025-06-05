# 📄 core/loader.py
# Заменим вызов extract_files_from_archive() временно — архивы отключены

import os
from utils.file_utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_pptx,
    extract_text_from_xlsx,
    extract_text_from_odf,
    extract_text_from_html,
    extract_text_from_txt,
    extract_text_from_image
)
from typing import Optional

def load_file(path: str) -> str:
    ext = os.path.splitext(path)[-1].lower()
    
    # ❌ Временно отключаем архивы
    if ext in [".zip", ".rar", ".7z"]:
        raise NotImplementedError("Обработка архивов временно отключена. Установите компилятор MSVC.")

    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    elif ext == ".pptx":
        return extract_text_from_pptx(path)
    elif ext == ".xlsx":
        return extract_text_from_xlsx(path)
    elif ext == ".odt":
        return extract_text_from_odf(path)
    elif ext in [".html", ".htm"]:
        return extract_text_from_html(path)
    elif ext in [".txt", ".md"]:
        return extract_text_from_txt(path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return extract_text_from_image(path)
    else:
        raise ValueError(f"Неподдерживаемый тип файла: {ext}")
    
    
def load_file_to_knowledge(path: str, session_id: Optional[str] = None):
    print(f"[DEBUG] Загрузка файла в базу знаний: {path}, session: {session_id}")
    content = load_file(path)
    # Здесь можно вызвать split_into_chunks(), embedder, extractor и т.д.
    return content

def parallel_load_files(folder: str, session_id: Optional[str] = None):
    print(f"[DEBUG] Параллельная загрузка из папки: {folder}, session: {session_id}")
    for root, _, files in os.walk(folder):
        for f in files:
            try:
                load_file_to_knowledge(os.path.join(root, f), session_id)
            except Exception as e:
                print(f"[ERROR] Ошибка при обработке {f}: {e}")