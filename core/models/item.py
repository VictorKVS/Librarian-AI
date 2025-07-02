# core/models/item.py

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property
from core.models.database import Base

if TYPE_CHECKING:
    from core.models.category import Category
    from core.models.tag import Tag

# Миксин с временными метками (если ещё не создан)
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Время создания")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Время обновления")

class Item(TimestampMixin, Base):
    __tablename__ = "items"
    __table_args__ = (
        Index(
            'idx_item_name_trgm',
            'name',
            postgresql_using='gin',
            postgresql_ops={'name': 'gin_trgm_ops'}
        ),
        {'comment': 'Таблица элементов/товаров системы'}
    )

    id = Column(Integer, primary_key=True, index=True, comment="Идентификатор элемента")
    name = Column(String(255), unique=True, nullable=False, comment="Наименование элемента")
    description = Column(Text, nullable=True, comment="Описание элемента")
    price = Column(Integer, nullable=True, comment="Цена в копейках")
    status = Column(String(20), default='active', nullable=False, comment="Статус элемента")

    # Связь «многие-к-одному» с Category
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), index=True, comment="ID категории")
    category = relationship("Category", back_populates="items")

    # Связь «многие-ко-многим» с Tag через item_tags
    tags: List["Tag"] = relationship(
        "Tag",
        secondary="item_tags",
        back_populates="items"
    )

    # Валидация статуса
    @validates('status')
    def validate_status(self, key, status):
        allowed = ['active', 'archived', 'draft']
        if status not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return status

    # Гибридное свойство для цены в рублях
    @hybrid_property
    def price_rub(self) -> Optional[float]:
        return self.price / 100 if self.price is not None else None

    @price_rub.setter
    def price_rub(self, value: Optional[float]):
        self.price = int(value * 100) if value is not None else None

    # Класс-метод для поиска по имени
    @classmethod
    def get_by_name(cls, db: Session, name: str) -> Optional["Item"]:
        return db.query(cls).filter(cls.name == name).first()

    @classmethod
    def search(cls, db: Session, query: str, limit: int = 10) -> List["Item"]:
        return db.query(cls).filter(
            cls.name.ilike(f"%{query}%") |
            cls.description.ilike(f"%{query}%")
        ).limit(limit).all()

    # Обновление из словаря
    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    # Сериализация в dict
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price_rub,
            'status': self.status,
            'category_id': self.category_id,
            'tags': [tag.name for tag in self.tags],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, name='{self.name}', status='{self.status}')>"
