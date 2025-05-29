# 📄 Файл: embedder.py | Расположение: librarian_ai/core/embedder.py
# 📌 Назначение: векторизация текстов и сохранение эмбеддингов для FAISS
# 📥 Получает: списки текстов (и метаданных)
# 📤 Передаёт: numpy-векторы, индекс FAISS и метаинформацию

from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import os
import pickle

class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        """
        Векторизация списка текстов
        :param texts: List[str]
        :return: np.array векторов
        """
        return self.model.encode(texts, convert_to_numpy=True)

    def save_index(self, vectors, metadata, index_path="knowledge/vector_store/index.faiss", meta_path="knowledge/vector_store/meta.pkl"):
        """
        Сохраняет FAISS-индекс и метаданные
        :param vectors: np.array
        :param metadata: List[dict]
        """
        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(vectors)
        faiss.write_index(index, index_path)

        with open(meta_path, "wb") as f:
            pickle.dump(metadata, f)

        print(f"💾 Индекс сохранён в {index_path}, метаданные — в {meta_path}")


if __name__ == "__main__":
    texts = ["информационная безопасность", "персональные данные", "ГОСТ 57580"]
    meta = [
        {"source": "doc1.txt", "text": texts[0]},
        {"source": "doc2.txt", "text": texts[1]},
        {"source": "doc3.txt", "text": texts[2]},
    ]
    embedder = Embedder()
    vecs = embedder.encode(texts)
    embedder.save_index(vecs, meta)
