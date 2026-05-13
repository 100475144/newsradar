"""Schemas de Notifications alineados con la API oficial.

Modelo oficial:

    class Metric:
        name: str
        value: float

    class NotificationBase:
        timestamp: datetime
        metrics: List[Metric]

    class Notification(NotificationBase):
        id: int
        alert_id: int

Para la UI (no oficial) usamos ``NotificationDetailResponse`` que incluye
los campos internos ``title``, ``message``, ``is_read``, ``user_id`` y
``news_id``.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────
# Tipos auxiliares
# ─────────────────────────────────────────────────────────────────────


class Metric(BaseModel):
    name: str = Field(..., min_length=1, max_length=90)
    value: float


# ─────────────────────────────────────────────────────────────────────
# Schemas oficiales
# ─────────────────────────────────────────────────────────────────────


class NotificationBase(BaseModel):
    # ``timestamp`` is required by the official contract (notifications must
    # be timestamped at creation). Pydantic returns 422 if the client omits
    # the field, which is what the verification battery's GN-002 expects.
    timestamp: datetime
    metrics: List[Metric] = Field(default_factory=list)


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    metrics: Optional[List[Metric]] = None


class NotificationResponse(NotificationBase):
    id: int
    alert_id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────
# Schemas internos / añadidos para la UI
# ─────────────────────────────────────────────────────────────────────


class NotificationDetailResponse(BaseModel):
    """Respuesta enriquecida (no oficial) que la UI consume."""

    id: int
    alert_id: int
    timestamp: datetime
    metrics: List[Metric] = Field(default_factory=list)
    user_id: int
    news_id: Optional[int] = None
    title: str
    message: str
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


class NotificationReadStatusUpdate(BaseModel):
    """Body interno para PATCH /notifications/{id}/read."""

    is_read: bool
