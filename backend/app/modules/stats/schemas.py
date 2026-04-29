"""Schemas de Stats alineados con la API oficial."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.notifications.schemas import Metric


class StatsBase(BaseModel):
    metrics: List[Metric] = Field(default_factory=list)


class StatsCreate(StatsBase):
    pass


class StatsUpdate(BaseModel):
    metrics: Optional[List[Metric]] = None


class StatsResponse(StatsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
