"""Modelos del módulo alerts: se definirán las entidades/tablas ORM relacionadas con alertas de usuario."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Alert(Base):
    """Minimal alert entity prepared for user ownership.

    Sprint 1 scope: only define ownership relationship with users.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User")