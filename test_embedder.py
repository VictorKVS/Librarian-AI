# test_embedder.py

import os
import sys

# Добавляем корень проекта в sys.path, чтобы Python увидел папку core/
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from core.tools.embedder import EmbeddingService

def main():
    # Инициализируем сервис эмбеддингов
    service = EmbeddingService(model_name="all-MiniLM-L6-v2", device="cpu")

    # Тест одного текста
    single = service.embed_text("Это тестовое предложение для эмбеддинга.")
    print(f"Размер вектора: {len(single)}, первые 5 значений: {single[:5]}")

    # Тест пакетной обработки
    texts = [
        "Первый текст для эмбеддинга.",
        "Второй текст для проверки батчевого режима.",
        "Третий текст, чтобы увидеть результат."
    ]
    batch = service.embed_batch(texts, batch_size=2)
    print(f"Эмбеддинги батча имеют форму: {len(batch)}×{len(batch[0])}")
    for i, vec in enumerate(batch):
        print(f" Текст {i+1}, первые 3 координаты: {vec[:3]}")

if __name__ == "__main__":
    main()
