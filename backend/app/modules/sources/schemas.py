"""Sources schemas for Sprint 1 auth preparation."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
	name: str = Field(..., min_length=1, max_length=120)
	url: str = Field(..., min_length=1, max_length=2048)


class SourceCreate(SourceBase):
	"""Creation contract kept minimal until Sprint 2 CRUD work."""


class SourceResponse(SourceBase):
	id: int
	is_active: bool = True
	created_by: int

	model_config = ConfigDict(from_attributes=True)


class SourceUpdate(BaseModel):
	name: Optional[str] = Field(default=None, min_length=1, max_length=120)
	url: Optional[str] = Field(default=None, min_length=1, max_length=2048)
	is_active: Optional[bool] = None
