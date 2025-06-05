# 📄 Файл: entity_extractor.py
# 📂 Путь установки: librarian_ai/core/entity_extractor.py

import re
import logging
import concurrent.futures
import natasha
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

try:
    import spacy
except ImportError:
    spacy = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Entity:
    label: str
    text: str
    value: str
    context: Optional[str] = None
    confidence: Optional[float] = None

class EntityExtractor:
    def __init__(self, lang: str = "ru", custom_patterns: Optional[Dict[str, str]] = None,
                 enable_multiprocessing: bool = True):
        self.lang = lang
        self.custom_patterns = custom_patterns or {}
        self.enable_multiprocessing = enable_multiprocessing
        self._init_nlp_models()
        self._normalization_cache = {}
        self.extraction_stats = defaultdict(int)

    def _init_nlp_models(self):
        self.models = {}
        try:
            if self.lang == "ru":
                try:
                    from natasha import Segmenter, MorphVocab, NamesExtractor, AddrExtractor, OrgExtractor, DateExtractor
                    self.segmenter = Segmenter()
                    self.morph_vocab = MorphVocab()
                    self.models = {
                        "PERSON": NamesExtractor(self.morph_vocab),
                        "ORG": OrgExtractor(self.morph_vocab),
                        "LOC": AddrExtractor(self.morph_vocab),
                        "DATE": DateExtractor(self.morph_vocab)
                    }
                    logger.info("Natasha models loaded successfully")
                except ImportError:
                    logger.warning("Natasha not available, falling back to regex only")
                    self.models = {}

            elif self.lang in ["en", "multi"]:
                model_name = "en_core_web_sm" if self.lang == "en" else "xx_ent_wiki_sm"
                try:
                    import spacy
                    try:
                        self.nlp = spacy.load(model_name)
                    except OSError:
                        logger.warning(f"spaCy model {model_name} not found, downloading...")
                        from spacy.cli import download
                        download(model_name)
                        self.nlp = spacy.load(model_name)
                except ImportError:
                    logger.warning("spaCy not available, falling back to regex only")
                    self.nlp = None

            elif self.lang == "de":
                try:
                    import spacy
                    self.nlp = spacy.load("de_core_news_sm")
                    logger.info("Loaded German spaCy model")
                except:
                    logger.warning("German model not available")

            elif self.lang == "fr":
                try:
                    import spacy
                    self.nlp = spacy.load("fr_core_news_sm")
                    logger.info("Loaded French spaCy model")
                except:
                    logger.warning("French model not available")

        except Exception as e:
            logger.error(f"Critical error during model initialization: {str(e)}")
            self.models = {}
            self.nlp = None

    def _extract_with_spacy(self, text: str) -> List[Entity]:
        if not hasattr(self, 'nlp') or self.nlp is None:
            return []
        doc = self.nlp(text)
        return [Entity(label=ent.label_, text=ent.text, value=ent.text,
                       context=self._get_context(text, ent.start_char, ent.end_char), confidence=0.9)
                for ent in doc.ents]

    def _extract_with_natasha(self, text: str) -> List[Entity]:
        if not self.models:
            return []
        doc = natasha.Doc(text)
        doc.segment(self.segmenter)
        entities = []
        for label, extractor in self.models.items():
            for match in extractor(text):
                span = match.span
                value = match.fact.as_json if hasattr(match.fact, 'as_json') else str(match.fact)
                entities.append(Entity(
                    label=label,
                    text=text[span[0]:span[1]],
                    value=value,
                    context=self._get_context(text, *span),
                    confidence=0.85
                ))
        return entities

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

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        return text[max(0, start - window):min(len(text), end + window)]

    def _normalize_entity(self, entity: Entity) -> Entity:
        cache_key = f"{entity.label}:{entity.text.lower()}"
        if cache_key in self._normalization_cache:
            return self._normalization_cache[cache_key]

        norm_text = entity.text
        norm_value = entity.value

        if entity.label in ["PERSON", "PER"]:
            parts = [p.strip() for p in re.split(r'\s+', norm_value) if p.strip()]
            if len(parts) > 1:
                norm_value = f"{parts[0]} {'.'.join([p[0] for p in parts[1:] if p])}."

        elif entity.label in ["ORG", "ORGANIZATION"]:
            norm_value = re.sub(r'\b(LLC|Inc|Corp|Ltd|ООО|АО|ЗАО)\b', '', norm_value, flags=re.IGNORECASE)
            norm_value = re.sub(r'[^\w\s]', '', norm_value).strip().title()

        elif entity.label == "DATE":
            try:
                from dateutil.parser import parse
                dt = parse(norm_value)
                norm_value = dt.strftime("%Y-%m-%d")
            except:
                pass

        norm_entity = Entity(
            label=entity.label,
            text=norm_text,
            value=norm_value,
            context=entity.context,
            confidence=entity.confidence
        )
        self._normalization_cache[cache_key] = norm_entity
        return norm_entity

    def _post_process(self, entities: List[Entity]) -> List[Entity]:
        normalized = [self._normalize_entity(e) for e in entities]
        seen = set()
        unique = []
        for e in normalized:
            key = (e.label, e.value.lower())
            if key not in seen:
                seen.add(key)
                unique.append(e)
                self.extraction_stats[e.label] += 1
        return unique

    def extract_entities(self, text: str) -> List[Entity]:
        import time
        logger.info(f"Starting entity extraction for text: {text[:50]}...")
        start_time = time.time()
        try:
            raw = []
            if self.lang == "ru" and self.models:
                raw += self._extract_with_natasha(text)
            elif self.lang in ["en", "multi", "de", "fr"] and hasattr(self, 'nlp'):
                raw += self._extract_with_spacy(text)
            raw += self._extract_custom(text)
            processed = self._post_process(raw)
            logger.info(f"Extracted {len(processed)} entities in {time.time() - start_time:.2f}s")
            return processed
        except Exception as e:
            logger.error(f"Error during entity extraction: {str(e)}")
            return []

    def batch_extract(self, texts: List[str]) -> List[List[Entity]]:
        if not self.enable_multiprocessing or len(texts) < 5:
            return [self.extract_entities(t) for t in texts]
        with concurrent.futures.ProcessPoolExecutor() as executor:
            return list(executor.map(self.extract_entities, texts))

    def get_stats(self) -> Dict[str, int]:
        return dict(self.extraction_stats)