# core/models/category.py

from typing import List
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from core.models.database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {
        "comment": "Таблица категорий для элементов"
    }

    id = Column(Integer, primary_key=True, index=True, comment="Идентификатор категории")
    name = Column(String(100), unique=True, nullable=False, comment="Название категории")
    description = Column(Text, nullable=True, comment="Описание категории")

    # Связь one-to-many: одна категория — много items
    items: List["Item"] = relationship("Item", back_populates="category", cascade="all, delete", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"