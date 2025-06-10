# core/processor/retriever.py
# 📄 core/retriever.py
# 📌 Назначение: Расширенный семантический поиск с кэшированием и гибридным поиском

from typing import List, Dict, Tuple, Optional, Union
import faiss
import numpy as np
import os
import pickle
import logging
import hashlib
from datetime import datetime
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json

from core.tools.embedder import Embedder
from db.storage import SessionStorage

class Retriever:
    def __init__(self, 
                 index_path: str = "knowledge/vector_store/index.faiss",
                 meta_path: str = "knowledge/vector_store/meta.pkl",
                 cache_size: int = 1000):
        self.embedder = Embedder()
        self.index_path = index_path
        self.meta_path = meta_path
        self.session_storage = SessionStorage()
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._cache_size = cache_size
        self._verify_paths()
        self._load_resources()

    def _verify_paths(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        if not os.path.exists(self.index_path):
            self._create_empty_index()
        if not os.path.exists(self.meta_path):
            with open(self.meta_path, "wb") as f:
                pickle.dump([], f)

    def _create_empty_index(self):
        dim = self.embedder.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(dim)
        faiss.write_index(self.index, self.index_path)

    def _load_resources(self):
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
            if len(self.metadata) != self.index.ntotal:
                self.logger.warning("Расхождение в количестве векторов и метаданных!")
                self._rebuild_index_metadata()
            self.logger.info(f"Загружен индекс с {self.index.ntotal} векторами")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки: {str(e)}")
            raise

    def _rebuild_index_metadata(self):
        self.logger.warning("Перестроение метаданных индекса...")
        self.metadata = [{"vector_id": i} for i in range(self.index.ntotal)]
        self._save_metadata()

    def _save_metadata(self):
        temp_path = self.meta_path + ".tmp"
        with open(temp_path, "wb") as f:
            pickle.dump(self.metadata, f)
        os.replace(temp_path, self.meta_path)

    @lru_cache(maxsize=1000)
    def _get_query_cache_key(self, query: str, filters: Optional[Dict]) -> str:
        filter_str = json.dumps(filters, sort_keys=True) if filters else ""
        return hashlib.md5((query + filter_str).encode()).hexdigest()

    async def retrieve(self, query: str, top_k: int = 5, session_id: Optional[str] = None, filters: Optional[Dict] = None, hybrid: bool = False, alpha: float = 0.5) -> List[Dict]:
        try:
            cache_key = self._get_query_cache_key(query, filters)
            if hasattr(self, '_cache') and cache_key in self._cache:
                return self._cache[cache_key][:top_k]

            if hybrid:
                results = await self._hybrid_search(query, top_k, filters, alpha)
            else:
                results = await self._semantic_search(query, top_k * 3, filters)

            if session_id:
                await self._log_search(session_id, query, results)

            if not hasattr(self, '_cache'):
                self._cache = {}
            self._cache[cache_key] = results

            return results[:top_k]

        except Exception as e:
            self.logger.error(f"Ошибка поиска: {str(e)}", exc_info=True)
            raise

    async def _semantic_search(self, query: str, top_k: int, filters: Optional[Dict] = None) -> List[Dict]:
        loop = asyncio.get_event_loop()
        query_vec = await loop.run_in_executor(self.executor, lambda: self.embedder.encode([query]))
        query_np = np.array(query_vec).astype("float32")
        distances, indices = await loop.run_in_executor(self.executor, lambda: self.index.search(query_np, top_k))
        return self._process_results(indices[0], distances[0], filters)

    async def _hybrid_search(self, query: str, top_k: int, filters: Optional[Dict] = None, alpha: float = 0.5) -> List[Dict]:
        semantic, keyword = await asyncio.gather(
            self._semantic_search(query, top_k, filters),
            self._keyword_search(query, top_k, filters)
        )
        return self._combine_results(semantic, keyword, alpha)

    async def _keyword_search(self, query: str, top_k: int, filters: Optional[Dict] = None) -> List[Dict]:
        """Поиск по ключевым словам в метаданных"""
        keywords = query.lower().split()
        results = []
        for idx, meta in enumerate(self.metadata):
            text = json.dumps(meta).lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                meta_copy = meta.copy()
                meta_copy.update({"score": score, "vector_id": idx, "timestamp": datetime.now().isoformat()})
                if not filters or self._match_filters(meta_copy, filters):
                    results.append(meta_copy)
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def _combine_results(self, semantic_results: List[Dict], keyword_results: List[Dict], alpha: float) -> List[Dict]:
        combined = {}
        sem_scores = [r["score"] for r in semantic_results]
        kw_scores = [r["score"] for r in keyword_results]
        max_sem = max(sem_scores) if sem_scores else 1
        max_kw = max(kw_scores) if kw_scores else 1

        for r in semantic_results:
            doc_id = r["vector_id"]
            combined[doc_id] = {**r, "combined_score": alpha * (r["score"] / max_sem)}

        for r in keyword_results:
            doc_id = r["vector_id"]
            if doc_id in combined:
                combined[doc_id]["combined_score"] += (1 - alpha) * (r["score"] / max_kw)
            else:
                combined[doc_id] = {**r, "combined_score": (1 - alpha) * (r["score"] / max_kw)}

        return sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)

    def _process_results(self, indices: np.ndarray, distances: np.ndarray, filters: Optional[Dict] = None) -> List[Dict]:
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._process_single_result, idx, score, filters)
                for idx, score in zip(indices, distances)
                if idx < len(self.metadata)
            ]
            return [f.result() for f in futures if f.result() is not None]

    def _process_single_result(self, idx: int, score: float, filters: Optional[Dict] = None) -> Optional[Dict]:
        meta = self.metadata[idx].copy()
        if filters and not self._match_filters(meta, filters):
            return None
        meta.update({
            "score": float(score),
            "vector_id": int(idx),
            "timestamp": datetime.now().isoformat()
        })
        return meta

    def _match_filters(self, meta: Dict, filters: Dict) -> bool:
        for key, value in filters.items():
            if meta.get(key) != value:
                return False
        return True

    async def _log_search(self, session_id: str, query: str, results: List[Dict]):
        search_data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "top_result": results[0] if results else None,
            "result_count": len(results),
            "retrieved_ids": [r["vector_id"] for r in results[:10]]
        }
        await self.session_storage.update_session_async(session_id, search_history=search_data)

    async def update_index(self, new_vectors: List[np.ndarray], new_metadata: List[Dict], batch_size: int = 1000):
        try:
            if len(new_vectors) != len(new_metadata):
                raise ValueError("Количество векторов и метаданных не совпадает")

            for i in range(0, len(new_vectors), batch_size):
                batch_vectors = new_vectors[i:i + batch_size]
                batch_meta = new_metadata[i:i + batch_size]
                vectors = np.array(batch_vectors).astype("float32")
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.index.add(vectors)
                )
                self.metadata.extend(batch_meta)
                self.logger.info(f"Добавлено {len(batch_vectors)} векторов")

            await self._save_index()

        except Exception as e:
            self.logger.error(f"Ошибка обновления: {str(e)}", exc_info=True)
            raise

    async def _save_index(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            lambda: faiss.write_index(self.index, self.index_path)
        )
        await loop.run_in_executor(
            self.executor,
            self._save_metadata
        )

    def __del__(self):
        self.executor.shutdown()
        if hasattr(self, '_cache'):
            del self._cache