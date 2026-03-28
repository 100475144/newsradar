"""Sources models for Sprint 1 auth preparation."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Source(Base):
	"""Minimal source entity prepared for user ownership.

	Sprint 1 scope: only define ownership relationship with users.
	"""

	__tablename__ = "sources"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	url = Column(String, nullable=False)
	is_active = Column(Boolean, default=True, nullable=False)

	created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	owner = relationship("User")
