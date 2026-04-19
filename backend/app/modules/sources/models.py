"""Sources models for Sprint 2 CRUD."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Source(Base):
	"""RSS source owned by a user."""

	__tablename__ = "sources"
	__table_args__ = (UniqueConstraint("url", "created_by", name="uq_sources_url_created_by"),)

	id = Column(Integer, primary_key=True, index=True)
	medium_name = Column(String(120), nullable=False, index=True)
	name = Column(String, nullable=False)
	url = Column(String, nullable=False, index=True)
	category = Column(String(255), nullable=True, index=True)
	is_active = Column(Boolean, default=True, nullable=False)

	created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	owner = relationship("User")

	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
