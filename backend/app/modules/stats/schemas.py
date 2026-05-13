"""Schemas de Stats alineados con la API oficial."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.notifications.schemas import Metric


class StatsBase(BaseModel):
    metrics: List[Metric]


class StatsCreate(StatsBase):
    @field_validator("metrics")
    @classmethod
    def validate_metrics_not_empty(cls, value: List[Metric]) -> List[Metric]:
        if not value:
            raise ValueError("Metrics list cannot be empty.")
        return value


class StatsUpdate(BaseModel):
    metrics: Optional[List[Metric]] = None


class StatsResponse(StatsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
