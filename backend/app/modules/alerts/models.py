"""Modelo Alert alineado con la API oficial.

Cambios respecto a la versión anterior (T6.4):
- ``expanded_keywords`` → ``descriptors``.
- ``category: str`` → ``categories: List[{code, label}]`` JSONB.
- ``source_ids: List[int]`` se reemplaza por dos campos JSONB de strings:
  ``rss_channels_ids`` e ``information_sources_ids``.
- ``created_by`` → ``user_id``.
- Se conservan campos internos (``keyword``, ``notify_in_app``,
  ``notify_email``, ``is_active``) que NO aparecen en la API oficial pero
  son necesarios para nuestro flujo de matching y notificaciones.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)

    # Campos del schema oficial.
    descriptors = Column(JSONB, nullable=False, default=list)
    categories = Column(JSONB, nullable=False, default=list)
    rss_channels_ids = Column(JSONB, nullable=False, default=list)
    information_sources_ids = Column(JSONB, nullable=False, default=list)
    cron_expression = Column(String(120), nullable=False, default="*/5 * * * *")

    # Owner (alineado con ``Alert.user_id`` del oficial).
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Campos internos (no en API oficial).
    keyword = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    notify_in_app = Column(Boolean, nullable=False, default=True)
    notify_email = Column(Boolean, nullable=False, default=False)

    owner = relationship("User")
