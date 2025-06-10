## -*- coding: utf-8 -*-
# core/tools/__init__.py
"""
Пакет утилит и инструментов ядра приложения.
Экспортирует основные классы и модули для быстрого доступа.
"""

# ——— Celery-таски ———
# Предполагается, что в core/tools/async_tasks.py есть:
#   celery_app  – экземпляр Celery
#   create_status_task – хотя бы "заглушка" (см. комментарий ниже)
from .async_tasks import celery_app, create_status_task

# ——— Класс для генерации эмбеддингов ———
# В вашем core/tools/embedder.py класс называется EmbeddingService.
# Поэтому здесь мы импортируем его под тем же именем:
from .embedder import EmbeddingService

# ——— Извлечение сущностей (NER) ———
# Предположим, что в core/tools/extractor.py есть функция extract_entities
from .extractor import extract_entities

# ——— Утилиты для графа знаний ———
# Если в core/tools/graph_tools.py есть класс GraphTools
from .graph_tools import GraphTools

# ——— Загрузка и анализ файлов ———
# Предположим, что в core/tools/loader.py есть FileLoader и/или SmartLoader
from .loader import FileLoader, SmartLoader

# ——— Генерация аннотаций/резюме ———
# Предположим, что в core/tools/summary_generator.py есть SummaryGenerator и generate_summary
from .summary_generator import SummaryGenerator, generate_summary

# ——— Семантический поиск по чанкам ———
# Предположим, что в core/tools/semantic_search.py есть SemanticSearch и/или semantic_search
from .semantic_search import SemanticSearch, semantic_search

# ——— Извлечение текста из архивов ———
# Предположим, что в core/tools/archive_extractors.py есть функции extract_from_archive и класс ArchiveExtractor
from .archive_extractors import extract_from_archive, ArchiveExtractor

__all__ = [
    # async-таски
    "celery_app", "create_status_task",
    # эмбеддер
    "EmbeddingService",
    # извлечение сущностей
    "extract_entities",
    # граф-утилиты
    "GraphTools",
    # загрузчик файлов
    "FileLoader", "SmartLoader",
    # генератор резюме
    "SummaryGenerator", "generate_summary",
    # семантический поиск
    "SemanticSearch", "semantic_search",
    # архивные извлекатели
    "extract_from_archive", "ArchiveExtractor",
]