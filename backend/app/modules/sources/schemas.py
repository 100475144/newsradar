"""Sources schemas for Sprint 2 CRUD."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceBase(BaseModel):
	name: str = Field(..., min_length=1, max_length=120)
	url: HttpUrl


class SourceCreate(SourceBase):
	"""Creation payload for a source."""


class SourceUpdate(BaseModel):
	name: Optional[str] = Field(default=None, min_length=1, max_length=120)
	url: Optional[HttpUrl] = None
	is_active: Optional[bool] = None


class SourceResponse(SourceBase):
	id: int
	is_active: bool = True
	created_by: int
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)
