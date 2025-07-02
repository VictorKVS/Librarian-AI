# core/tools/archive_extractors.py
import zipfile
import os

def extract_text_from_zip(zip_path: str, extract_to: str) -> list:
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Not a valid ZIP archive")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)
    # TODO: прочитать извлечённые файлы и вернуть список текстов
    return []