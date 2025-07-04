# 📄 Файл: agent_cli.py
# 📂 Путь: cli/
# 📌 Назначение: Командная оболочка для загрузки файлов, извлечения эмбеддингов и сущностей

import argparse
import os
from core.loader import load_file_to_knowledge, parallel_load_files
from core.embedder import embed_chunks
from core.entity_extractor import extract_entities
from utils.file_utils import process_directory_recursively
from db.storage import session_scope
from db.models import KnowledgeDoc

# 🧠 Поддержка генерации через локальную LLM
from providers.mistral_local import MistralLocal

def process_file(path: str):
    print(f"📄 Обработка файла: {path}")
    docs = load_file_to_knowledge(path)
    docs = docs if isinstance(docs, list) else [docs]
    print(f"✅ Загружено {len(docs)} фрагментов текста")

    for doc in docs:
        # 📌 Эмбеддинг
        embed_chunks([doc])
        # 🧠 Извлечение сущностей
        with session_scope() as session:
            extract_entities(session, doc)

def process_folder(folder: str):
    print(f"📂 Обработка директории: {folder}")
    paths = process_directory_recursively(folder)
    print(f"🔍 Найдено {len(paths)} файлов")
    docs = parallel_load_files(paths)
    all_docs = [doc for d in docs for doc in (d if isinstance(d, list) else [d])]
    print(f"✅ Загружено {len(all_docs)} документов")

    # 📌 Эмбеддинг и извлечение
    embed_chunks(all_docs)
    with session_scope() as session:
        for doc in all_docs:
            extract_entities(session, doc)

def run_mistral_cli():
    print("🧠 Запуск локальной LLM (Mistral)...")
    llm = MistralLocal()
    while True:
        prompt = input(">>> ")
        if prompt.lower() in ("exit", "quit"): break
        response = llm.generate(prompt)
        print(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="📚 Обработка файла или папки с документами или запуск LLM")
    parser.add_argument("--file", type=str, help="Путь к файлу")
    parser.add_argument("--folder", type=str, help="Путь к директории")
    parser.add_argument("--llm", action="store_true", help="Запустить локальную LLM Mistral")

    args = parser.parse_args()

    if args.llm:
        run_mistral_cli()
    elif args.file:
        process_file(args.file)
    elif args.folder:
        process_folder(args.folder)
    else:
        print("⚠️ Укажите --file, --folder или --llm")
