"""Modelo Notification alineado con la API oficial.

Modelo oficial:

    class Notification:
        id: int
        alert_id: int
        timestamp: datetime
        metrics: List[Metric]

Mantenemos campos internos no expuestos en la API canónica para soportar la
UI: ``title``, ``message``, ``user_id`` (destinatario), ``news_id``,
``is_read``.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "alert_id", "news_id", name="uq_notification_user_alert_news"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Campos del schema oficial.
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    metrics = Column(JSONB, nullable=False, default=list)

    # FKs.
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)

    # Campos internos (no en API oficial pero usados por la UI).
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)

    owner = relationship("User")
    alert = relationship("Alert")
    news = relationship("News")
