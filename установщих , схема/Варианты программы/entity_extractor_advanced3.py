# 📄 Файл: entity_extractor_advanced.py
# Содержит полную реализацию улучшенного EntityExtractor с поддержкой:
# - Конфигурации YAML/JSON
# - Расширенной нормализации
# - Кэширования
# - Пользовательских словарей
# - Подключаемых плагинов
# - Метрик и телеметрии

# !!! Этот код предполагает, что основные методы класса реализованы ранее !!!
# Здесь представлены только ключевые улучшения и архитектура

# Импорты
import re
import yaml
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from functools import lru_cache
from entity_extractor import Entity  # предполагается наличие базового Entity

logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self, lang: str = "ru", custom_patterns: Optional[Dict[str, str]] = None,
                 enable_multiprocessing: bool = True, enable_caching: bool = True,
                 custom_dicts: Optional[Dict[str, List[str]]] = None, plugins: List[str] = None):
        self.lang = lang
        self.custom_patterns = custom_patterns or {}
        self.enable_multiprocessing = enable_multiprocessing
        self._cache_enabled = enable_caching
        self.custom_dicts = custom_dicts or {}
        self.plugins = []
        self._normalization_cache = {}
        self.extraction_stats = defaultdict(int)
        self._setup_telemetry()
        self._init_nlp_models()
        self._load_custom_dicts()
        self._load_plugins(plugins or [])

    @classmethod
    def from_config(cls, config_path: str):
        config_path = Path(config_path)
        if config_path.suffix == '.yaml':
            with open(config_path) as f:
                config = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path) as f:
                config = json.load(f)
        else:
            raise ValueError("Unsupported config format. Use YAML or JSON")

        return cls(
            lang=config.get('language', 'ru'),
            custom_patterns=config.get('patterns', {}),
            enable_multiprocessing=config.get('multiprocessing', True),
            enable_caching=config.get('caching', True),
            custom_dicts=config.get('custom_dicts', {}),
            plugins=config.get('plugins', [])
        )

    def _setup_telemetry(self):
        self.telemetry = {
            'extraction_time': 0.0,
            'processed_chars': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    @lru_cache(maxsize=1000)
    def _cached_extract(self, text: str) -> List[Entity]:
        return self._raw_extract(text)

    def extract_entities(self, text: str) -> List[Entity]:
        if not text or not isinstance(text, str):
            return []
        return self._cached_extract(text) if self._cache_enabled else self._raw_extract(text)

    def _normalize_entity(self, entity: Entity) -> Entity:
        cache_key = f"{entity.label}:{entity.text.lower()}"
        if cache_key in self._normalization_cache:
            return self._normalization_cache[cache_key]

        norm_value = entity.value
        try:
            if entity.label == "DATE":
                from dateutil.parser import parse
                norm_value = parse(norm_value, fuzzy=True).strftime("%Y-%m-%d")
            elif entity.label in ["MONEY", "QUANTITY"]:
                from babel.numbers import parse_decimal
                norm_value = str(parse_decimal(norm_value.replace(",", ".")))
            elif entity.label in ["ORG", "ORGANIZATION"]:
                norm_value = re.sub(r'\b(LLC|Inc|Corp|Ltd|ООО|АО|ЗАО)\b', '', norm_value, flags=re.IGNORECASE)
                norm_value = re.sub(r'[^\w\s]', '', norm_value).strip().title()
            elif entity.label in ["PERSON", "PER"]:
                parts = norm_value.split()
                if len(parts) > 1:
                    norm_value = f"{parts[0]} {'.'.join(p[0] for p in parts[1:] if p)}."
        except Exception as e:
            logger.warning(f"Normalization error: {str(e)}")

        normalized = Entity(label=entity.label, text=entity.text, value=norm_value,
                            context=entity.context, confidence=entity.confidence)
        self._normalization_cache[cache_key] = normalized
        return normalized

    def _load_custom_dicts(self):
        self.dict_patterns = {}
        for label, entries in self.custom_dicts.items():
            pattern = r"\b(" + "|".join(re.escape(entry) for entry in entries) + r")\b"
            self.dict_patterns[label] = re.compile(pattern, re.IGNORECASE)

    def _extract_from_dicts(self, text: str) -> List[Entity]:
        entities = []
        for label, pattern in self.dict_patterns.items():
            for match in pattern.finditer(text):
                entities.append(Entity(
                    label=label,
                    text=match.group(),
                    value=match.group(),
                    context=None,
                    confidence=0.95
                ))
        return entities

    def _load_plugins(self, plugin_paths: List[str]):
        for path in plugin_paths:
            try:
                from importlib import import_module
                plugin = import_module(path)
                if hasattr(plugin, 'initialize'):
                    self.plugins.append(plugin.initialize(self))
                    logger.info(f"Loaded plugin: {path}")
            except Exception as e:
                logger.error(f"Failed to load plugin {path}: {str(e)}")

    def _extract_with_plugins(self, text: str) -> List[Entity]:
        results = []
        for plugin in self.plugins:
            if hasattr(plugin, 'extract'):
                try:
                    results += plugin.extract(text)
                except Exception as e:
                    logger.error(f"Plugin extract error: {str(e)}")
        return results

    def _raw_extract(self, text: str) -> List[Entity]:
        raw = []
        if hasattr(self, "_extract_with_natasha"):
            raw += self._extract_with_natasha(text)
        if hasattr(self, "_extract_with_spacy"):
            raw += self._extract_with_spacy(text)
        raw += self._extract_from_dicts(text)
        raw += self._extract_with_plugins(text)
        return [self._normalize_entity(e) for e in raw]
