# librarian_ai/llm/__init__.py

"""
Подпакет llm:
Содержит маршрутизатор LLM и, при необходимости, другие классы-обёртки для разных провайдеров.
"""

# Экспортируем по умолчанию роутер, чтобы можно было писать:
#   from librarian_ai.llm import LLMRouter, LLMProvider
from .llm_router import LLMRouter, LLMProvider, default_router, query_llm

__all__ = [
    "LLMRouter",
    "LLMProvider",
    "default_router",
    "query_llm",
]