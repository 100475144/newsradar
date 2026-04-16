"""Schemas del módulo alerts: se definirán los modelos de entrada/salida para validar requests y responses de alertas."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    keyword: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=255)
    expanded_keywords: List[str] = Field(default_factory=list, max_length=10)
    notify_in_app: bool = True
    notify_email: bool = False
    source_id: Optional[int] = None

    @field_validator("expanded_keywords")
    @classmethod
    def validate_expanded_keywords(cls, value: List[str]) -> List[str]:
        cleaned = []
        seen = set()

        for item in value:
            item = item.strip()
            if not item:
                continue
            lowered = item.lower()
            if lowered not in seen:
                seen.add(lowered)
                cleaned.append(item)

        if cleaned and not (3 <= len(cleaned) <= 10):
            raise ValueError("expanded_keywords must contain between 3 and 10 items.")

        return cleaned


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, min_length=1, max_length=255)
    expanded_keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None
    source_id: Optional[int] = None

    @field_validator("expanded_keywords")
    @classmethod
    def validate_expanded_keywords(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value

        cleaned = []
        seen = set()

        for item in value:
            item = item.strip()
            if not item:
                continue
            lowered = item.lower()
            if lowered not in seen:
                seen.add(lowered)
                cleaned.append(item)

        if cleaned and not (3 <= len(cleaned) <= 10):
            raise ValueError("expanded_keywords must contain between 3 and 10 items.")

        return cleaned


class AlertResponse(BaseModel):
    id: int
    name: str
    keyword: str
    expanded_keywords: list[str]
    category: str
    is_active: bool
    notify_in_app: bool
    notify_email: bool
    created_by: int
    source_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
