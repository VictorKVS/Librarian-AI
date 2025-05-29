# 📄 Файл: entity_extractor_advanced.py
# 📂 Путь установки: librarian_ai/core/entity_extractor_advanced.py

import re
import json
import yaml
import time
import logging
import concurrent.futures
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from pathlib import Path
from functools import lru_cache
from importlib import import_module

try:
    import natasha
except ImportError:
    natasha = None

try:
    import spacy
except ImportError:
    spacy = None

@dataclass
class Entity:
    label: str
    text: str
    value: str
    context: Optional[str] = None
    confidence: Optional[float] = None

logging.basicConfig(level=logging.INFO)
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
        self._init_nlp_models()
        self._load_custom_dicts()
        self._load_plugins(plugins or [])
        self._normalization_cache = {}
        self.extraction_stats = defaultdict(int)
        self._setup_telemetry()
    def _setup_telemetry(self):
        self.telemetry = {
            'extraction_time': 0.0,
            'processed_chars': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

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

    def _init_nlp_models(self):
        self.models = {}
        try:
            if self.lang == "ru" and natasha:
                self.segmenter = natasha.Segmenter()
                self.morph_vocab = natasha.MorphVocab()
                self.models = {
                    "PERSON": natasha.NamesExtractor(self.morph_vocab),
                    "ORG": natasha.OrgExtractor(self.morph_vocab),
                    "LOC": natasha.AddrExtractor(self.morph_vocab),
                    "DATE": natasha.DateExtractor(self.morph_vocab)
                }
            elif self.lang in ["en", "multi", "de", "fr"] and spacy:
                model_map = {
                    "en": "en_core_web_sm",
                    "multi": "xx_ent_wiki_sm",
                    "de": "de_core_news_sm",
                    "fr": "fr_core_news_sm"
                }
                model_name = model_map.get(self.lang, "en_core_web_sm")
                try:
                    self.nlp = spacy.load(model_name)
                except OSError:
                    from spacy.cli import download
                    download(model_name)
                    self.nlp = spacy.load(model_name)
            else:
                self.nlp = None
        except Exception as e:
            logger.error(f"Failed to init NLP models: {e}")
            self.models = {}
            self.nlp = None
    def _load_custom_dicts(self):
        self.dict_patterns = {}
        for label, entries in self.custom_dicts.items():
            pattern = r"\b(" + "|".join(re.escape(e) for e in entries) + r")\b"
            self.dict_patterns[label] = re.compile(pattern, flags=re.IGNORECASE)

    def _load_plugins(self, plugin_paths):
        self.plugins = []
        for path in plugin_paths:
            try:
                module = import_module(path)
                if hasattr(module, 'initialize'):
                    self.plugins.append(module.initialize(self))
            except Exception as e:
                logger.warning(f"Plugin {path} failed: {e}")

    def _extract_with_natasha(self, text: str) -> List[Entity]:
        if not self.models:
            return []
        doc = natasha.Doc(text)
        doc.segment(self.segmenter)
        results = []
        for label, extractor in self.models.items():
            for match in extractor(text):
                span = match.span
                val = getattr(match.fact, 'as_json', str(match.fact))
                results.append(Entity(label=label, text=text[span[0]:span[1]], value=str(val),
                                      context=self._get_context(text, *span), confidence=0.85))
        return results

    def _extract_with_spacy(self, text: str) -> List[Entity]:
        if not hasattr(self, 'nlp') or self.nlp is None:
            return []
        doc = self.nlp(text)
        return [Entity(label=ent.label_, text=ent.text, value=ent.text,
                       context=self._get_context(text, ent.start_char, ent.end_char), confidence=0.9)
                for ent in doc.ents]
    def _extract_custom(self, text: str) -> List[Entity]:
        entities = []
        for label, pattern in self.custom_patterns.items():
            for match in re.finditer(pattern, text):
                entities.append(Entity(
                    label=label,
                    text=match.group(),
                    value=match.group(),
                    context=self._get_context(text, *match.span()),
                    confidence=1.0
                ))
        return entities

    def _extract_from_dicts(self, text: str) -> List[Entity]:
        entities = []
        for label, pattern in self.dict_patterns.items():
            for match in pattern.finditer(text):
                entities.append(Entity(
                    label=label,
                    text=match.group(),
                    value=match.group(),
                    context=self._get_context(text, *match.span()),
                    confidence=0.95
                ))
        return entities

    def _extract_with_plugins(self, text: str) -> List[Entity]:
        entities = []
        for plugin in self.plugins:
            if hasattr(plugin, 'extract'):
                try:
                    entities.extend(plugin.extract(text))
                except Exception as e:
                    logger.warning(f"Plugin error: {e}")
        return entities

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        return text[max(0, start - window):min(len(text), end + window)]
    def _normalize_entity(self, entity: Entity) -> Entity:
        key = f"{entity.label}:{entity.text.lower()}"
        if key in self._normalization_cache:
            return self._normalization_cache[key]
        norm_value = entity.value
        try:
            if entity.label in ["PERSON", "PER"]:
                parts = re.split(r'\s+', norm_value)
                if len(parts) > 1:
                    norm_value = f"{parts[0]} {'.'.join([p[0] for p in parts[1:] if p])}."
            elif entity.label in ["ORG", "ORGANIZATION"]:
                norm_value = re.sub(r'\b(LLC|Inc|Corp|Ltd|ООО|АО|ЗАО)\b', '', norm_value, flags=re.IGNORECASE)
                norm_value = re.sub(r'[^\w\s]', '', norm_value).strip().title()
            elif entity.label == "DATE":
                from dateutil.parser import parse
                dt = parse(norm_value, fuzzy=True)
                norm_value = dt.strftime("%Y-%m-%d")
            elif entity.label in ["MONEY", "QUANTITY"]:
                from babel.numbers import parse_decimal
                norm_value = str(parse_decimal(norm_value.replace(",", ".")))
        except:
            pass
        norm_entity = Entity(label=entity.label, text=entity.text, value=norm_value,
                             context=entity.context, confidence=entity.confidence)
        self._normalization_cache[key] = norm_entity
        return norm_entity

    def _post_process(self, entities: List[Entity]) -> List[Entity]:
        seen = set()
        result = []
        for e in map(self._normalize_entity, entities):
            key = (e.label, e.value.lower())
            if key not in seen:
                seen.add(key)
                result.append(e)
                self.extraction_stats[e.label] += 1
        return result
    @lru_cache(maxsize=1000)
    def _cached_extract(self, text: str) -> List[Entity]:
        return self._raw_extract(text)

    def _raw_extract(self, text: str) -> List[Entity]:
        raw = []
        if self.lang == "ru" and self.models:
            raw += self._extract_with_natasha(text)
        elif self.lang in ["en", "multi", "de", "fr"] and hasattr(self, 'nlp'):
            raw += self._extract_with_spacy(text)
        raw += self._extract_custom(text)
        raw += self._extract_from_dicts(text)
        raw += self._extract_with_plugins(text)
        return self._post_process(raw)

    def extract_entities(self, text: str) -> List[Entity]:
         if not text or not isinstance(text, str):
            return []

        start_time = time.time()
        result = self._cached_extract(text) if self._cache_enabled else self._raw_extract(text)
        elapsed_time = time.time() - start_time

        self._update_telemetry(elapsed_time, len(text))
        return result

    def batch_extract(self, texts: List[str]) -> List[List[Entity]]:
        if not self.enable_multiprocessing or len(texts) < 5:
            return [self.extract_entities(t) for t in texts]
        with concurrent.futures.ProcessPoolExecutor() as executor:
            return list(executor.map(self.extract_entities, texts))
    def _update_telemetry(self, elapsed_time: float, chars_processed: int):
        self.telemetry['extraction_time'] += elapsed_time
        self.telemetry['processed_chars'] += chars_processed
        self.telemetry['cache_hits'] = len(self._normalization_cache)
        self.telemetry['cache_misses'] = sum(v == 0 for v in self._normalization_cache.values())

    def get_telemetry(self) -> Dict[str, float]:
        return self.telemetry

    def reset_stats(self):
        self.extraction_stats.clear()
        self.telemetry = {
            'extraction_time': 0.0,
            'processed_chars': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self._normalization_cache.clear()

