"""Schemas del módulo crawler: se definirán los modelos de entrada/salida para lanzar procesos y devolver resultados."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceStub(BaseModel):
    id: int
    medium_name: str
    name: str
    url: str
    category: Optional[str] = None
    is_active: bool = True


class ParsedFeedItem(BaseModel):
    title: str = Field(..., min_length=1)
    link: str = Field(..., min_length=1)
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    external_id: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None


class CrawlResult(BaseModel):
    source_id: int
    source_name: str
    fetched_items: int
    stored_items: int
    duplicates_skipped: int
