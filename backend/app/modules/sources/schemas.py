"""Schemas para Category, InformationSource y RSSChannel.

Alineados con la API oficial proporcionada por el profesor.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# ─────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(default="IPTC", pattern="^IPTC$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty.")
        return value


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    source: Optional[str] = Field(default=None, pattern="^IPTC$")

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty.")
        return value


class CategoryResponse(CategoryBase):
    # ``id`` es el código IPTC oficial de 8 dígitos como string
    # (ej. "13000000"), tal y como esperan los smoke tests del aula global.
    id: str

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────
# InformationSource
# ─────────────────────────────────────────────────────────────────────


class InformationSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Information source name cannot be empty.")
        return value


class InformationSourceCreate(InformationSourceBase):
    pass


class InformationSourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    url: Optional[HttpUrl] = None

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Information source name cannot be empty.")
        return value


class InformationSourceResponse(InformationSourceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────
# RSSChannel
# ─────────────────────────────────────────────────────────────────────


class RSSChannelBase(BaseModel):
    url: HttpUrl
    # ``category_id`` es el código IPTC string (ej. "13000000").
    category_id: str = Field(..., min_length=1, max_length=8)


class RSSChannelCreate(RSSChannelBase):
    pass


class RSSChannelUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    category_id: Optional[str] = Field(default=None, min_length=1, max_length=8)


class RSSChannelResponse(RSSChannelBase):
    id: int
    information_source_id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────
# Catalog summary (mantenido como endpoint añadido para checklist #13-15)
# ─────────────────────────────────────────────────────────────────────


class SourceCatalogSummaryResponse(BaseModel):
    total_channels: int
    total_media_outlets: int
    iptc_categories_covered: int
    iptc_categories_total: int
    covers_all_iptc_categories: bool
