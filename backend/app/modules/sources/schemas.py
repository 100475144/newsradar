"""Sources schemas for Sprint 2 CRUD."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.iptc import IPTC_CATEGORIES, IPTC_CATEGORY_CODES


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl
    category: Optional[str] = Field(default=None, max_length=255, description="IPTC first-level category code")

    @field_validator("category")
    @classmethod
    def validate_iptc_category(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value and value not in IPTC_CATEGORIES:
            allowed = ", ".join(IPTC_CATEGORY_CODES)
            raise ValueError(
                f"Invalid IPTC category '{value}'. Must be one of: {allowed}"
            )
        return value


class SourceCreate(SourceBase):
    """Creation payload for a source."""


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    url: Optional[HttpUrl] = None
    category: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None

    @field_validator("category")
    @classmethod
    def validate_iptc_category(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value and value not in IPTC_CATEGORIES:
            allowed = ", ".join(IPTC_CATEGORY_CODES)
            raise ValueError(
                f"Invalid IPTC category '{value}'. Must be one of: {allowed}"
            )
        return value


class SourceResponse(SourceBase):
    id: int
    is_active: bool = True
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
