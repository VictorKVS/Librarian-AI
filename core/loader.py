# 📄 Файл: loader.py | Расположение: librarian_ai/core/loader.py
# 📌 Назначение: загрузка исходных документов в Librarian AI
# 📥 Получает: путь к папке с файлами (PDF, DOCX, TXT)
# 📤 Передаёт: чистый текст и метаданные в парсер/классификатор
# "Файл loader.py создан. Он отвечает за загрузку документов из указанной папки, фильтрует по расширениям и передаёт список файлов дальше в цепочку обработки."
import os

SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"]

def load_documents(folder_path):
    """
    Загружает поддерживаемые файлы из указанной директории.
    Возвращает список текстов или путей к файлам.
    """
    loaded = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, file)
                loaded.append(full_path)
    return loaded

if __name__ == "__main__":
    test = load_documents("../test_data")
    for path in test:
        print(f"📄 Найден файл: {path}")

