 core/models/item_tags.py

from sqlalchemy import Table, Column, Integer, ForeignKey
from core.models.database import Base

# Промежуточная таблица для связи многие-ко-многим между Item и Tag
item_tags = Table(
    "item_tags",
    Base.metadata,
    Column("item_id", Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True, comment="ID элемента"),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, comment="ID тега"),
    comment="Ассоциативная таблица для связи Item ↔ Tag"
)