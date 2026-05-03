"""Modelos del módulo alerts: entidades/tablas ORM relacionadas con alertas de usuario."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    keyword = Column(String(255), nullable=False)
    expanded_keywords = Column(JSONB, nullable=False, default=list)
    category = Column(String(255), nullable=False)
    source_ids = Column(JSONB, nullable=False, default=list)

    is_active = Column(Boolean, nullable=False, default=True)
    notify_in_app = Column(Boolean, nullable=False, default=True)
    notify_email = Column(Boolean, nullable=False, default=False)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship("User")
