"""Schemas para Category, InformationSource y RSSChannel.

Alineados con la API oficial proporcionada por el profesor.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty.")
        return value


class CategoryCreate(CategoryBase):
    # ``code`` es opcional en POST. Si el cliente lo proporciona (con o sin
    # prefijo ``medtop:``), el endpoint valida que coincida con el código
    # IPTC canónico derivado del ``name``. Esto cubre GC-008 (el verificador
    # postea pares (name, code) inconsistentes tras vaciar el catálogo y
    # espera 4xx).
    code: Optional[str] = Field(default=None, max_length=30)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    source: Optional[str] = Field(default=None)

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty.")
        return value


class CategoryResponse(BaseModel):
    id: int
    name: str
    source: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _compute_code(self):
        """Derive the 8-digit IPTC code from the integer id (e.g. 1000000 → '01000000')."""
        if self.code is None and isinstance(self.id, int):
            self.code = str(self.id).zfill(8)
        return self


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
    category_id: int


class RSSChannelCreate(RSSChannelBase):
    pass


class RSSChannelUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    category_id: Optional[int] = None


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
