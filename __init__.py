# librarian_ai/__init__.py

"""
Пакет librarian_ai:
- Содержит код для работы с LLM (в папке llm)
- Утилиты (в папке tools)
- Экспорт «главных» классов и функций на верхнем уровне пакета
"""

__version__ = "0.1.0"

# === Экспорт классов/функций из llm ===
from .llm.llm_router import (
    LLMRouter,
    LLMProvider,
    default_router,
    query_llm,
)

# Если у вас есть базовые клиенты в llm/base_llm.py или local_model.py, можно их тоже здесь экспортировать:
# from .llm.base_llm import BaseLLMClient
# from .llm.local_model import LocalModelClient

# === Экспорт утилит из tools ===
from .tools.embedder import Embedder, EmbeddingType, CacheInfo
from .tools.loader import SmartLoader

__all__ = [
    # llm
    "LLMRouter",
    "LLMProvider",
    "default_router",
    "query_llm",
    # "BaseLLMClient",
    # "LocalModelClient",
    # tools
    "Embedder",
    "EmbeddingType",
    "CacheInfo",
    "SmartLoader",
]
