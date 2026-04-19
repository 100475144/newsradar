"""Schemas del módulo news: se definirán los modelos de entrada/salida para validar requests y responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    link: str = Field(..., min_length=1, max_length=1000)
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = Field(default=None, max_length=120)
    classification_origin: str = Field(default="unknown", max_length=20)
    language: Optional[str] = Field(default=None, max_length=10)
    author: Optional[str] = Field(default=None, max_length=255)


class NewsCreateInternal(NewsBase):
    source_id: Optional[int] = None
    external_id: Optional[str] = Field(default=None, max_length=255)
    content_hash: Optional[str] = Field(default=None, max_length=64)


class NewsResponse(NewsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: Optional[int] = None
    external_id: Optional[str] = None
    content_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NewsListResponse(BaseModel):
    items: list[NewsResponse]
    total: int
