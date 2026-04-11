"""Schemas del módulo notifications: se definirán los modelos de entrada/salida para validar requests y responses de notificaciones."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    is_read: bool
    created_by: int

    model_config = ConfigDict(from_attributes=True)
    