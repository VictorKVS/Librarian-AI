from typing import List
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

class VectorRetriever:
    def __init__(self, vector_store_path="knowledge/vector_store/index.faiss",
                 metadata_path="knowledge/vector_store/meta.pkl",
                 model_name="all-MiniLM-L6-v2"):
        self.vector_store_path = vector_store_path
        self.metadata_path = metadata_path
        self.model = SentenceTransformer(model_name)

        # Загрузка индекса
        if not os.path.exists(self.vector_store_path):
            raise FileNotFoundError(f"Индекс не найден: {self.vector_store_path}")
        self.index = faiss.read_index(self.vector_store_path)

        # Загрузка метаданных
        with open(self.metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Возвращает top_k наиболее релевантных документов (или chunks)
        """
        query_vec = self.model.encode([query])
        D, I = self.index.search(np.array(query_vec).astype("float32"), top_k)

        results = []
        for i in I[0]:
            if i < len(self.metadata):
                results.append(self.metadata[i])
        return results


if __name__ == "__main__":
    retriever = VectorRetriever()
    result = retriever.retrieve("медицинская безопасность данных", top_k=3)
    for doc in result:
        print(f"📄 {doc['source']}\n{textwrap.shorten(doc['text'], width=200)}\n")
