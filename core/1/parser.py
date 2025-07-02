# 📄 Файл: parser.py | Расположение: librarian_ai/core/parser.py
# 📌 Назначение: извлечение текста и метаданных из файлов
# 📥 Получает: список путей к файлам (от loader.py)
# 📤 Передаёт: чистый текст и метаинформацию (название, дата, автор и пр.)
# Файл parser.py создан. Он извлекает текст и базовую метаинформацию (имя, размер) из .txt-файлов. Позже можно подключить поддержку PDF, DOCX и HTML.

import os

# TODO: подключить парсеры PDF, DOCX, HTML при необходимости

def parse_text_file(filepath):
    """
    Извлекает текст из обычного .txt файла.
    :param filepath: путь к файлу
    :return: словарь с текстом и метаинформацией
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        meta = {
            "filename": os.path.basename(filepath),
            "size_kb": round(os.path.getsize(filepath) / 1024, 2)
        }
        return {"text": text, "meta": meta}
    except Exception as e:
        return {"error": str(e), "path": filepath}


if __name__ == "__main__":
    from pprint import pprint
    test = parse_text_file("../test_data/example.txt")
    pprint(test)
