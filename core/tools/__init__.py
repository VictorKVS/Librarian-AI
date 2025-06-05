# -*- coding: utf-8 -*-
# core/tools/__init__.py
"""
Пакет утилит и инструментов ядра приложения.
Экспортирует основные классы и модули для быстрого доступа.
"""

# Регистрируем подпакеты и модули
# Celery-таски
from .async_tasks import celery_app, create_status_task  # поправьте имена под ваши реализации

# Класс для генерации эмбеддингов
from .embedder import Embedder, EmbeddingType, CacheInfo

# Извлечение сущностей (NER)
from .extractor import extract_entities

# Утилиты для графа знаний
from .graph_tools import GraphTools  # или нужные вам классы/функции

# Загрузка и анализ файлов
from .loader import SmartLoader, FileLoader

# Генерация аннотаций/резюме
from .summary_generator import SummaryGenerator, generate_summary

# Семантический поиск по чанкам
from .semantic_search import SemanticSearch, semantic_search

# Извлечение текста из архивов
from .archive_extractors import extract_from_archive, ArchiveExtractor

__all__ = [
    # async-таски
    "celery_app", "create_status_task",
    # эмбеддер
    "Embedder", "EmbeddingType", "CacheInfo",
    # извлекатель сущностей
    "extract_entities",
    # граф-утилиты
    "GraphTools",
    # загрузчик файлов
    "SmartLoader", "FileLoader",
    # генератор резюме
    "SummaryGenerator", "generate_summary",
    # семантический поиск
    "SemanticSearch", "semantic_search",
    # архивные извлекатели
    "extract_from_archive", "ArchiveExtractor",
]