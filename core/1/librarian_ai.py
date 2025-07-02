# 📄 Файл: re_ranker.py
# 📂 Путь установки: librarian_ai/core/re_ranker.py
# 📌 Назначение: повторное ранжирование (Re-Ranking) результатов поиска
# 📥 Получает: список кандидатов от retriever (векторный поиск)
# ⚙️ Делает: пересчитывает релевантность с помощью CrossEncoder (или модели rerank)
# 📤 Передаёт: отсортированные по убыванию релевантности фрагменты (в LLM или визуализацию)

# 🚨 Потенциальные улучшения:
# 1. 📘 Выбор оптимальной модели CrossEncoder (например, ruBERT, DeepPavlov для РФ)
# 2. 🔄 Оптимизация: batched rerank, многопоточность, кэширование
# 3. 🇷🇺 Поддержка русского языка через мультиязычные модели
# 4. 🔬 Предобработка: удаление пунктуации, лемматизация, стоп-слова

from typing import List, Dict
from sentence_transformers import CrossEncoder
import string
from pymorphy2 import MorphAnalyzer

morph = MorphAnalyzer()

class ReRanker:
    def __init__(self, model_name="DeepPavlov/rubert-base-cased-conversational"):
        self.model = CrossEncoder(model_name)

    def lemmatize(self, word: str) -> str:
        """Приводит слово к нормальной форме."""
        return morph.parse(word)[0].normal_form

    def preprocess(self, text: str) -> str:
        """Нормализация текста: лемматизация, очистка от пунктуации и цифр."""
        words = text.split()
        clean_words = [self.lemmatize(w) for w in words if w.isalpha()]
        return ' '.join(clean_words)

    def rerank(self, query: str, docs: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Ранжирует документы по релевантности.
        :param query: исходный запрос
        :param docs: список документов с ключом 'text'
        :param top_k: количество топ-документов
        :return: список top_k документов по убыванию релевантности
        """
        query_clean = self.preprocess(query)
        pairs = [[query_clean, self.preprocess(doc["text"])] for doc in docs]
        scores = self.model.predict(pairs)

        for i, score in enumerate(scores):
            docs[i]["score"] = float(score)

        return sorted(docs, key=lambda x: x["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    reranker = ReRanker()
    query = "обработка персональных данных"
    candidates = [
        {"text": "Персональные данные должны храниться согласно 152-ФЗ."},
        {"text": "Шифрование — ключевой механизм защиты."},
        {"text": "Персональные данные включают ФИО, СНИЛС и адрес проживания."}
    ]
    top = reranker.rerank(query, candidates)
    for doc in top:
        print(f"⭐ {doc['score']:.4f} | {doc['text']}")
