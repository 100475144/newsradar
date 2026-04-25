"""Sources schemas for Sprint 2 CRUD."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.iptc import IPTC_CATEGORIES, IPTC_CATEGORY_CODES


class SourceBase(BaseModel):
    medium_name: str = Field(..., min_length=1, max_length=120, description="Media outlet that owns the RSS channel")
    name: str = Field(..., min_length=1, max_length=120, description="RSS channel or section name")
    url: HttpUrl
    category: Optional[str] = Field(default=None, max_length=255, description="IPTC first-level category code")

    @field_validator("medium_name", "name")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or blank.")
        return value

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
    medium_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    url: Optional[HttpUrl] = None
    category: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None

    @field_validator("medium_name", "name")
    @classmethod
    def validate_optional_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty or blank.")
        return value

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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceCatalogSummaryResponse(BaseModel):
    total_channels: int
    total_media_outlets: int
    iptc_categories_covered: int
    iptc_categories_total: int
    covers_all_iptc_categories: bool
