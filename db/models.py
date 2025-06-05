# 📄 Файл: models.py
# 📂 Путь: db/
# 📌 Назначение: Оптимизированные ORM-модели для PostgreSQL с pgvector и расширенной аналитикой

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, ForeignKey, Float, Boolean,
    Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship, validates
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
import re
from datetime import datetime

Base = declarative_base()


# ----------------- Общие миксины -----------------
class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ----------------- Лог сессий -----------------
class SessionLog(Base, TimestampMixin):
    __tablename__ = "session_logs"
    __table_args__ = (
        Index('ix_session_logs_user_id_created_at', 'user_id', 'created_at'),
        Index('ix_session_logs_platform_created_at', 'platform', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), index=True, nullable=False)
    platform = Column(String(32), nullable=False)  # CLI, Web, Telegram, API
    session_state = Column(String(32), default='active')  # active, completed, timeout
    input_text = Column(Text)
    response = Column(Text)
    context = Column(JSONB)
    language = Column(String(8))
    processing_time = Column(Float)

    entities = relationship("EntityRecord", back_populates="session", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="session", cascade="all, delete-orphan", uselist=False)
    memory_accesses = relationship("MemoryAccessLog", back_populates="session")

    @validates('platform')
    def validate_platform(self, key, platform):
        assert platform in ['CLI', 'Web', 'Telegram', 'API', 'Mobile']
        return platform


# ----------------- Сущности -----------------
class EntityRecord(Base, TimestampMixin):
    __tablename__ = "entities"
    __table_args__ = (
        Index('ix_entities_label_text', 'label', 'text'),
        Index('ix_entities_normalized_value', 'normalized_value'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String(64), nullable=False)
    text = Column(String(512), nullable=False)
    normalized_value = Column(String(512))
    context = Column(Text)
    confidence = Column(Float, nullable=False)
    metadata = Column(JSONB)
    is_sensitive = Column(Boolean, default=False)
    categories = Column(ARRAY(String(32)))

    session_id = Column(UUID(as_uuid=True), ForeignKey("session_logs.id", ondelete="CASCADE"), nullable=False)
    session = relationship("SessionLog", back_populates="entities")
    memory_refs = relationship("MemoryItem", secondary="entity_memory_links", passive_deletes=True)

    @validates('confidence')
    def validate_confidence(self, key, confidence):
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return confidence


# ----------------- Элементы памяти -----------------
class MemoryItem(Base, TimestampMixin):
    __tablename__ = "memory_items"
    __table_args__ = (
        Index('ix_memory_items_embedding', 'embedding', postgresql_using='ivfflat'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    content_hash = Column(String(64), unique=True)
    metadata = Column(JSONB)
    last_accessed = Column(DateTime, default=func.now())
    access_count = Column(Integer, default=0)
    tags = Column(ARRAY(String(32)))

    doc_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_docs.id", ondelete="CASCADE"))
    document = relationship("KnowledgeDoc", back_populates="memories")
    access_logs = relationship("MemoryAccessLog", back_populates="memory_item")

    def update_access(self):
        self.last_accessed = func.now()
        self.access_count += 1


# ----------------- Документы знаний -----------------
class KnowledgeDoc(Base, TimestampMixin):
    __tablename__ = "knowledge_docs"
    __table_args__ = (
        Index('ix_knowledge_docs_source_path', 'source_path'),
        Index('ix_knowledge_docs_processed', 'processed'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(256), nullable=False)
    content = Column(Text)
    source_path = Column(String(512), unique=True)
    source_type = Column(String(32))  # pdf, docx, html, email, etc.
    processed = Column(Boolean, default=False)
    processing_errors = Column(Text)
    metadata = Column(JSONB)
    checksum = Column(String(64))
    version = Column(Integer, default=1)

    memories = relationship("MemoryItem", back_populates="document", cascade="all, delete-orphan")

    @validates('source_path')
    def validate_source_path(self, key, path):
        if not re.match(r'^[a-zA-Z0-9_\-\.\/]+$', path):
            raise ValueError("Invalid source path")
        return path


# ----------------- Обратная связь -----------------
class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session_logs.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer)
    comment = Column(Text)
    corrections = Column(JSONB)
    is_resolved = Column(Boolean, default=False)
    feedback_type = Column(String(32))  # praise, correction, complaint

    session = relationship("SessionLog", back_populates="feedback")

    @validates('rating')
    def validate_rating(self, key, value):
        if value is not None and not (1 <= value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return value


# ----------------- Связь Entity <-> Memory -----------------
class EntityMemoryLink(Base):
    __tablename__ = "entity_memory_links"
    __table_args__ = (
        Index('ix_entity_memory_links_relation', 'relation_type'),
    )

    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="CASCADE"), primary_key=True)
    relation_type = Column(String(32), nullable=False)  # mentioned_in, related_to, etc.
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


# ----------------- Лог доступа к памяти -----------------
class MemoryAccessLog(Base):
    __tablename__ = "memory_access_logs"
    __table_args__ = (
        Index('ix_memory_access_logs_session_memory', 'session_id', 'memory_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session_logs.id", ondelete="CASCADE"), nullable=False)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id", ondelete="CASCADE"), nullable=False)
    access_type = Column(String(32))  # read, write, update
    access_context = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("SessionLog", back_populates="memory_accesses")
    memory_item = relationship("MemoryItem", back_populates="access_logs")
