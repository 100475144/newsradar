"""Schemas del módulo alerts: modelos de entrada/salida para validar requests y responses de alertas."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.iptc import IPTC_CATEGORIES, IPTC_CATEGORY_CODES


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    keyword: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=255)
    expanded_keywords: List[str] = Field(default_factory=list, max_length=10)
    source_ids: List[int] = Field(default_factory=list, description="IDs of RSS sources to monitor (empty = all)")
    notify_in_app: bool = True
    notify_email: bool = False

    @field_validator("category")
    @classmethod
    def validate_iptc_category(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in IPTC_CATEGORIES:
            allowed = ", ".join(IPTC_CATEGORY_CODES)
            raise ValueError(
                f"Invalid IPTC category '{value}'. Must be one of: {allowed}"
            )
        return value

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
    source_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None

    @field_validator("category")
    @classmethod
    def validate_iptc_category(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in IPTC_CATEGORIES:
            allowed = ", ".join(IPTC_CATEGORY_CODES)
            raise ValueError(
                f"Invalid IPTC category '{value}'. Must be one of: {allowed}"
            )
        return value

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
    source_ids: list[int]
    is_active: bool
    notify_in_app: bool
    notify_email: bool
    created_by: int

    model_config = ConfigDict(from_attributes=True)
