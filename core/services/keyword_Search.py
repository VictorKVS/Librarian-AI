import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KeywordSearchResult:
    doc_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = None

class KeywordSearch:
    """
    Полнофункциональная реализация поиска по ключевым словам с использованием SQLite FTS5.
    Поддерживает:
    - Создание и обслуживание индексов
    - Гибкий поиск с подсветкой результатов
    - Фильтрацию по метаданным
    - Настройку ранжирования
    """
    
    def __init__(self, index_path: str, enable_highlighting: bool = True):
        """
        :param index_path: путь к файлу SQLite
        :param enable_highlighting: включить подсветку совпадений в результатах
        """
        self.index_path = index_path
        self.enable_highlighting = enable_highlighting
        self.conn = self._init_connection()
        
    def _init_connection(self) -> sqlite3.Connection:
        """Инициализирует соединение с SQLite и настраивает FTS"""
        conn = sqlite3.connect(self.index_path)
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Проверяем наличие FTS5
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fts_docs'")
        if not cursor.fetchone():
            self._create_fts_table(conn)
        
        return conn
    
    def _create_fts_table(self, conn: sqlite3.Connection) -> None:
        """Создает таблицу FTS5 с поддержкой метаданных"""
        conn.execute("""
        CREATE VIRTUAL TABLE fts_docs USING fts5(
            doc_id UNINDEXED,
            content,
            metadata UNINDEXED,
            tokenize='porter unicode61'
        )
        """)
        logger.info("Создана новая таблица FTS5")
    
    def index_document(self, doc_id: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Индексирует документ в FTS
        :param doc_id: уникальный идентификатор документа
        :param content: текстовое содержимое для индексации
        :param metadata: дополнительные метаданные в формате JSON
        """
        metadata_json = json.dumps(metadata or {})
        self.conn.execute(
            "INSERT INTO fts_docs (doc_id, content, metadata) VALUES (?, ?, ?)",
            (doc_id, content, metadata_json)
        )
        self.conn.commit()
    
    def batch_index(self, documents: List[Dict[str, Any]]) -> None:
        """Пакетная индексация документов"""
        with self.conn:
            self.conn.executemany(
                "INSERT INTO fts_docs (doc_id, content, metadata) VALUES (?, ?, ?)",
                [(doc['id'], doc['content'], json.dumps(doc.get('metadata', {}))) for doc in documents]
            )
    
    def search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None,
        min_score: float = 0.1
    ) -> List[KeywordSearchResult]:
        """
        Выполняет поиск по ключевым словам с возможностью фильтрации
        
        :param query: поисковый запрос (поддерживает FTS5 синтаксис)
        :param limit: максимальное количество результатов
        :param metadata_filter: фильтр по метаданным в формате {"field": "value"}
        :param min_score: минимальный порог релевантности
        :return: список результатов поиска
        """
        base_query = """
        SELECT 
            doc_id, 
            {highlight} AS text, 
            bm25(fts_docs) AS score,
            metadata
        FROM fts_docs
        WHERE fts_docs MATCH ?
        {filter_clause}
        ORDER BY score
        LIMIT ?
        """
        
        # Подготовка SQL с учетом фильтров
        filter_clause = ""
        params = [query]
        
        if metadata_filter:
            filter_conditions = []
            for field, value in metadata_filter.items():
                filter_conditions.append(f"json_extract(metadata, '$.{field}') = ?")
                params.append(str(value))
            filter_clause = "AND " + " AND ".join(filter_conditions)
        
        # Подсветка результатов
        highlight = (
            "snippet(fts_docs, -1, '<mark>', '</mark>', '...', 64)" 
            if self.enable_highlighting 
            else "content"
        )
        
        sql = base_query.format(highlight=highlight, filter_clause=filter_clause)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params + [limit])
            results = []
            
            for row in cursor.fetchall():
                if row[2] < min_score:  # Пропускаем низкорелевантные
                    continue
                
                results.append(KeywordSearchResult(
                    doc_id=row[0],
                    text=row[1],
                    score=row[2],
                    metadata=json.loads(row[3]) if row[3] else {}
                ))
            
            return results[:limit]
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка поиска: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str) -> None:
        """Удаляет документ из индекса"""
        self.conn.execute("DELETE FROM fts_docs WHERE doc_id = ?", (doc_id,))
        self.conn.commit()
    
    def optimize_index(self) -> None:
        """Оптимизирует индекс для повышения производительности"""
        self.conn.execute("INSERT INTO fts_docs(fts_docs) VALUES('optimize')")
        self.conn.commit()
    
    def close(self) -> None:
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
