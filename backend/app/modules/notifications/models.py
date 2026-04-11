"""Modelos del módulo notifications: se definirán las entidades/tablas ORM relacionadas con notificaciones generadas por el sistema."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User")
    