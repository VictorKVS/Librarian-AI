# core/processor/document_processor.py

# core/processor/document_processor.py

import logging
from typing import List, Dict, Optional

from pydantic import BaseModel
from langdetect import detect, LangDetectException
from sentence_transformers import SentenceTransformer
from spacy.lang.ru import Russian
import spacy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Параметры по умолчанию для spaCy-моделей
DEFAULT_SPACY_MODELS = {
    "ru": Russian,
    "en": "en_core_web_sm",
    "es": "es_core_news_sm",
    "de": "de_core_news_sm",
    "fr": "fr_core_news_sm",
}


# Схемы данных
class DocumentChunk(BaseModel):
    """
    Модель для одного чанка документа:
    - chunk_id: уникальный идентификатор чанка
    - text: текст чанка
    - embedding: векторное представление
    - entities: список найденных сущностей
    - metadata: любые дополнительные метаданные (например, язык, заголовок документа)
    """
    chunk_id: str
    text: str
    embedding: List[float]
    entities: List[Dict[str, str]]
    metadata: Dict[str, str]


class ProcessedDocument(BaseModel):
    """
    Итоговая модель обработанного документа:
    - doc_id: уникальный идентификатор документа
    - chunks: список объектов DocumentChunk
    - title: опциональный заголовок документа
    - version: опциональная версия документа
    """
    doc_id: str
    chunks: List[DocumentChunk]
    title: Optional[str] = None
    version: Optional[str] = None


class DocumentProcessor:
    """
    Универсальный процессор документов с поддержкой мультиязычности:
    - Автоматическое определение языка
    - Динамическая загрузка spaCy-моделей
    - Разбиение на смысловые чанки
    - Генерация векторных эмбеддингов
    - Извлечение ИБ-специфичных сущностей (CVE, угрозы, роли и т.п.)
    """

    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        spacy_models_config: Optional[Dict[str, str]] = None
    ):
        """
        :param embedding_model_name: название модели SentenceTransformer для эмбеддингов
        :param spacy_models_config: кастомные пути к spaCy-моделям (ключ — код языка, значение — путь или класс)
                                   например: {"ru": "ru_core_news_lg", "en": "en_core_web_trf"}
        """
        # SentenceTransformer для эмбеддингов
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Конфигурация spaCy-моделей (расширяем DEFAULT_SPACY_MODELS)
        self.spacy_models = {**DEFAULT_SPACY_MODELS, **(spacy_models_config or {})}

        # NLP-движок будет загружаться динамически при обработке конкретного документа
        self.nlp = None  

        logger.info(f"DocumentProcessor инициализирован с эмбеддинговой моделью: {embedding_model_name}")

    def _detect_language(self, text: str) -> str:
        """
        Определяет язык входного текста (langdetect). 
        Если язык не поддерживается или не определён — возвращает 'en' по умолчанию.
        """
        try:
            lang = detect(text)
            return lang if lang in self.spacy_models else "en"
        except LangDetectException:
            logger.warning("Не удалось определить язык документа — используем 'en' по умолчанию")
            return "en"

    def _load_spacy_model(self, lang_code: str) -> None:
        """
        Загружает spaCy-модель для указанного языка. 
        Если в конфигурации спейси-моделей указана строка — используем spacy.load(...). 
        Если это класс (например, Russian) — инстанцируем класс.
        """
        try:
            model_spec = self.spacy_models.get(lang_code, "en_core_web_sm")
            if isinstance(model_spec, str):
                self.nlp = spacy.load(model_spec)
            else:
                # model_spec — это класс (например, Russian)
                self.nlp = model_spec()
            logger.debug(f"Загружена spaCy-модель для языка '{lang_code}'")
        except Exception as e:
            logger.error(f"Ошибка при загрузке spaCy-модели для '{lang_code}': {e}. Используем пустую модель.")
            self.nlp = spacy.blank(lang_code)

    def _add_security_entity_rules(self, lang_code: str) -> None:
        """
        Добавляет языкоспецифичные правила для извлечения ИБ-сущностей через EntityRuler.
        Общие паттерны: CVE, стандарты.
        Языковые паттерны: THREAT (угрозы), ROLE (роли ИБ-специалистов и т.д.).
        """
        if not self.nlp or "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler")
        else:
            ruler = self.nlp.get_pipe("entity_ruler")

        # Общие паттерны (применимы ко всем языкам)
        common_patterns = [
            {"label": "CVE", "pattern": [{"TEXT": {"REGEX": r"CVE-\d{4}-\d{4,7}"}}]},
            {"label": "STANDARD", "pattern": [{"TEXT": {"REGEX": r"(ISO|PCI DSS|GDPR|NIST|HIPAA|ФСТЭК|ФСБ)\s*\d+"}}]},
        ]

        # Языко-специфичные паттерны
        language_patterns = {
            "ru": [
                {"label": "THREAT", "pattern": [{"LOWER": {"IN": [
                    "sql injection", "xss", "ddos", "ransomware",
                    "фишинг", "apt", "bruteforce", "вредоносное по"
                ]}}]},
                {"label": "ROLE", "pattern": [{"LOWER": {"IN": [
                    "ciso", "dpo", "администратор безопасности",
                    "аудитор", "инженер иб"
                ]}}]},
            ],
            "en": [
                {"label": "THREAT", "pattern": [{"LOWER": {"IN": [
                    "sql injection", "xss", "ddos", "ransomware",
                    "phishing", "apt", "bruteforce", "malware"
                ]}}]},
                {"label": "ROLE", "pattern": [{"LOWER": {"IN": [
                    "ciso", "dpo", "security administrator",
                    "auditor", "security engineer"
                ]}}]},
            ],
            "es": [
                {"label": "THREAT", "pattern": [{"LOWER": {"IN": [
                    "inyección sql", "xss", "ddos", "ransomware",
                    "phishing", "apt", "fuerza bruta"
                ]}}]},
                {"label": "ROLE", "pattern": [{"LOWER": {"IN": [
                    "director de seguridad", "encargado de protección de datos",
                    "auditor", "ingeniero de seguridad"
                ]}}]},
            ],
            # Можно добавить 'de', 'fr' по аналогии
        }

        patterns = common_patterns + language_patterns.get(lang_code, [])
        ruler.add_patterns(patterns)
        logger.debug(f"Добавлены NER-правила для языка '{lang_code}'")

    def chunk_document(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Разбивает текст на «смысловые» чанки:
        - Сохраняет целостность абзацев
        - Если абзац длиннее chunk_size слов, разбивает его на подфрагменты
        - Объединяет соседние абзацы до тех пор, пока не достигнет chunk_size
        """
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks: List[str] = []
        current_chunk_words: List[str] = []
        current_len = 0

        for para in paragraphs:
            words = para.split()
            para_len = len(words)

            # Если сам абзац превышает chunk_size * 1.5, разбиваем его прямо здесь
            if para_len > chunk_size * 1.5:
                for i in range(0, para_len, chunk_size):
                    chunks.append(" ".join(words[i : i + chunk_size]))
                continue

            # Если добавление этого абзаца превысит chunk_size, «закрываем» текущий чанк
            if current_len + para_len > chunk_size and current_chunk_words:
                chunks.append(" ".join(current_chunk_words))
                current_chunk_words = []
                current_len = 0

            # Добавляем параграф в текущий чанк
            current_chunk_words.extend(words)
            current_len += para_len

        # Оставшийся чанк
        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))

        logger.debug(f"Текст разбит на {len(chunks)} чанков (chunk_size={chunk_size})")
        return chunks

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Запускает spaCy NLP-конвейер и извлекает найденные сущности в виде списка словарей:
        {
            "text": "<сущность>",
            "label": "<тип>",
            "start": <позиция начала>,
            "end": <позиция конца>
        }
        """
        doc = self.nlp(text)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]

    def generate_embeddings(self, text: str) -> List[float]:
        """
        Генерация векторного представления через SentenceTransformer.
        Возвращает list[float].
        """
        try:
            return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддингов: {e}")
            return []

    def process_document(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> ProcessedDocument:
        """
        Полный цикл обработки:
        1. Автоматическое определение языка
        2. Загрузка и настройка spaCy-модели
        3. Добавление правил для ИБ-сущностей
        4. Разбиение на чанки
        5. Для каждого чанка:
             - Генерация эмбеддингов
             - Извлечение сущностей
             - Формирование DocumentChunk
        6. Возврат ProcessedDocument Pydantic-модели
        """
        if not text:
            raise ValueError("Текст документа не может быть пустым")

        metadata = metadata.copy() if metadata else {}
        metadata.setdefault("doc_id", doc_id)

        # 1. Определяем язык
        lang = self._detect_language(text)
        metadata["lang"] = lang
        logger.info(f"Обработка документа '{doc_id}' (язык='{lang}')")

        # 2. Загрузка spaCy-модели
        self._load_spacy_model(lang)

        # 3. Добавляем правила для ИБ-сущностей
        self._add_security_entity_rules(lang)

        # 4. Разбиваем на чанки
        raw_chunks = self.chunk_document(text)

        processed_chunks: List[DocumentChunk] = []
        for idx, chunk_text in enumerate(raw_chunks):
            chunk_id = f"{doc_id}_chunk_{idx}"
            try:
                # 5.1. Генерируем эмбеддинги
                embedding = self.generate_embeddings(chunk_text)
                if not embedding:
                    continue

                # 5.2. Извлекаем сущности
                entities = self.extract_entities(chunk_text)

                # 5.3. Формируем объект DocumentChunk
                processed_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        embedding=embedding,
                        entities=entities,
                        metadata=metadata.copy(),
                    )
                )
            except Exception as e:
                logger.error(f"Ошибка при обработке чанка '{chunk_id}': {e}")
                continue

        logger.info(
            f"Документ '{doc_id}' успешно обработан, чанков: {len(processed_chunks)}"
        )
        return ProcessedDocument(
            doc_id=doc_id,
            chunks=processed_chunks,
            title=metadata.get("title"),
            version=metadata.get("version"),
        )
