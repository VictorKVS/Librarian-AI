# core/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class DocumentCreate(BaseModel):
    title: str
    content: str

class DocumentResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    chunks: List[str]