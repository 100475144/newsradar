"""Schemas del módulo notifications: se definirán los modelos de entrada/salida para validar requests y responses de notificaciones."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)


class NotificationCreate(NotificationBase):
    alert_id: int
    news_id: int


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    is_read: bool
    user_id: int
    alert_id: int
    news_id: int

    model_config = ConfigDict(from_attributes=True)
    