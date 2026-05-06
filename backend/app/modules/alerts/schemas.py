"""Schemas de Alertas alineados con la API oficial.

Modelo oficial (correo del profesor 29-abr):

    class AlertBase:
        name: str (max 200)
        descriptors: List[str]
        categories: List[AlertCategoryItem]
        rss_channels_ids: List[str]
        information_sources_ids: List[str]
        cron_expression: str (max 120)

Campos internos no expuestos en la API oficial pero mantenidos en BD para
nuestra UX: ``keyword``, ``notify_in_app``, ``notify_email``, ``is_active``.
"""

import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


CRON_REGEX = re.compile(
    r"^(\*|([0-5]?\d)(-([0-5]?\d))?(,([0-5]?\d)(-([0-5]?\d))?)*|(\*/\d+))"
    r"\s+(\*|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(,([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?)*|(\*/\d+))"
    r"\s+(\*|([12]?\d|3[01])(-([12]?\d|3[01]))?(,([12]?\d|3[01])(-([12]?\d|3[01]))?)*|(\*/\d+))"
    r"\s+(\*|(1[0-2]|[1-9])(-?(1[0-2]|[1-9]))?(,(1[0-2]|[1-9])(-?(1[0-2]|[1-9]))?)*|(\*/\d+))"
    r"\s+(\*|[0-6](-[0-6])?(,[0-6](-[0-6])?)*|(\*/\d+))$"
)


# ─────────────────────────────────────────────────────────────────────
# Tipos auxiliares
# ─────────────────────────────────────────────────────────────────────


class AlertCategoryItem(BaseModel):
    """Categoría asignada a una alerta. Replica el modelo oficial."""

    code: str = Field(..., min_length=1, max_length=60)
    label: str = Field(..., min_length=1, max_length=120)


# ─────────────────────────────────────────────────────────────────────
# Schemas oficiales
# ─────────────────────────────────────────────────────────────────────


class AlertBase(BaseModel):
    """Modelo oficial alineado con el ``main.py`` del aula global."""

    name: str = Field(..., min_length=1, max_length=200)
    descriptors: List[str] = Field(default_factory=list)
    categories: List[AlertCategoryItem] = Field(default_factory=list)
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
    cron_expression: str = Field(..., min_length=1, max_length=120)

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        value = value.strip()
        if not CRON_REGEX.match(value):
            raise ValueError(
                f"Invalid cron expression '{value}'. Expected standard 5-field cron."
            )
        return value

    @field_validator("descriptors")
    @classmethod
    def validate_descriptors(cls, value: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()
        for raw in value or []:
            term = (raw or "").strip()
            if not term:
                continue
            lowered = term.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            cleaned.append(term)
        return cleaned


# Mensaje de error compartido para descriptores fuera de rango. La spec
# oficial (smoke GA) exige entre 3 y 10 sinónimos por alerta.
DESCRIPTOR_COUNT_ERROR = (
    "descriptors must contain between 3 and 10 unique non-empty terms"
)
DESCRIPTOR_MIN = 3
DESCRIPTOR_MAX = 10


def _enforce_descriptor_count(value: List[str]) -> List[str]:
    if not (DESCRIPTOR_MIN <= len(value) <= DESCRIPTOR_MAX):
        raise ValueError(DESCRIPTOR_COUNT_ERROR)
    return value


class AlertCreateInternal(AlertBase):
    """Payload interno extendido para crear alertas desde la UI propia.

    Añade campos no presentes en la API oficial pero útiles para nuestro
    flujo de notificaciones (canales preferidos del usuario, keyword principal
    para matching, etc.).
    """

    keyword: Optional[str] = Field(default=None, min_length=1, max_length=200)
    notify_in_app: bool = True
    notify_email: bool = False

    @field_validator("descriptors", mode="after")
    @classmethod
    def enforce_count(cls, value: List[str]) -> List[str]:
        return _enforce_descriptor_count(value)


class AlertCreate(AlertBase):
    """Payload oficial para POST /users/{user_id}/alerts."""

    @field_validator("descriptors", mode="after")
    @classmethod
    def enforce_count(cls, value: List[str]) -> List[str]:
        return _enforce_descriptor_count(value)


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descriptors: Optional[List[str]] = None
    categories: Optional[List[AlertCategoryItem]] = None
    rss_channels_ids: Optional[List[str]] = None
    information_sources_ids: Optional[List[str]] = None
    cron_expression: Optional[str] = Field(default=None, min_length=1, max_length=120)
    # Campos internos opcionales:
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=200)
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not CRON_REGEX.match(value):
            raise ValueError(
                f"Invalid cron expression '{value}'. Expected standard 5-field cron."
            )
        return value

    @field_validator("descriptors")
    @classmethod
    def validate_descriptors(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        cleaned: List[str] = []
        seen: set[str] = set()
        for raw in value:
            term = (raw or "").strip()
            if not term:
                continue
            lowered = term.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            cleaned.append(term)
        # En update, si se proporciona descriptors debe estar en rango oficial.
        return _enforce_descriptor_count(cleaned)


class AlertResponse(AlertBase):
    """Respuesta oficial: ``AlertBase`` + ``id`` + ``user_id``.

    La respuesta incluye además los campos internos que nuestro frontend
    necesita para mostrar la alerta sin perder funcionalidad.
    """

    id: int
    user_id: int

    # Campos extra (no en la API oficial pero útiles para nuestra UI).
    keyword: Optional[str] = None
    notify_in_app: bool = True
    notify_email: bool = False
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
