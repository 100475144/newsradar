"""Schemas del módulo alerts: se definirán los modelos de entrada/salida para validar requests y responses de alertas."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertBase(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=255)


class AlertCreate(AlertBase):
    """Creation contract kept minimal until later sprints."""


class AlertResponse(AlertBase):
    id: int
    is_active: bool = True
    created_by: int

    model_config = ConfigDict(from_attributes=True)


class AlertUpdate(BaseModel):
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None