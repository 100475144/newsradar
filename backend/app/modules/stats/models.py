"""Modelo Stats alineado con la API oficial.

API oficial:
    class Stats:
        id: int
        metrics: List[Metric]   # cada Metric: {name, value}
"""

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class Stats(Base):
    """Snapshot de métricas. Útil para histórico de dashboard."""

    __tablename__ = "stats"

    id = Column(Integer, primary_key=True, index=True)
    metrics = Column(JSONB, nullable=False, default=list)

    # Timestamp interno (no expuesto en API canónica) para ordenar snapshots.
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
