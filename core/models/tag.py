# core/models/tag.py

from typing import List
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.models.database import Base

class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {
        "comment": "Таблица тегов для элементов"
    }

    id = Column(Integer, primary_key=True, index=True, comment="Идентификатор тега")
    name = Column(String(50), unique=True, nullable=False, comment="Название тега")

    # Связь many-to-many: тег может относиться к многим items
    items: List["Item"] = relationship(
        "Item",
        secondary="item_tags",
        back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"
