"""Modelos del catálogo de fuentes RSS.

Alineados con la API oficial (`main.py` aula global):
- ``Category`` (entidad propia con CRUD).
- ``InformationSource`` (medio: BBC, El País).
- ``RSSChannel`` (feed concreto que pertenece a un medio).

El antiguo modelo ``Source`` desaparece. ``News.source_id`` pasa a ser FK a
``rss_channels.id`` manteniendo los identificadores existentes para no
romper datos en producción/desarrollo (ver migración T6.3).
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Category(Base):
    """Categoría taxonómica de noticias.

    Por defecto IPTC primer nivel (17 categorías). El campo ``source``
    permite distinguir la taxonomía origen aunque actualmente solo se usa
    "IPTC".
    """

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    # ``id`` es el código IPTC oficial de 8 dígitos ("01000000"…"17000000").
    # Se usa string como PK para que la API exponga el código IPTC tal cual
    # esperan los smoke tests del aula global (SMOKE-005).
    id = Column(String(8), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    source = Column(String(20), nullable=False, default="IPTC")

    rss_channels = relationship("RSSChannel", back_populates="category")


class InformationSource(Base):
    """Medio de comunicación que agrupa varios canales RSS.

    Ejemplos: BBC, El País, Reuters.
    """

    __tablename__ = "information_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    url = Column(String(500), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    rss_channels = relationship(
        "RSSChannel",
        back_populates="information_source",
        cascade="all, delete-orphan",
    )


class RSSChannel(Base):
    """Canal RSS concreto que pertenece a un :class:`InformationSource`.

    Esta tabla sustituye a ``sources`` del modelo anterior. Mantiene los IDs
    para no invalidar las FKs de ``news.source_id``.
    """

    __tablename__ = "rss_channels"
    __table_args__ = (UniqueConstraint("url", name="uq_rss_channels_url"),)

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False, index=True)
    category_id = Column(
        String(8),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    information_source_id = Column(
        Integer,
        ForeignKey("information_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Campos internos (no expuestos en la API oficial pero útiles para UI/crawler).
    name = Column(String(255), nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    information_source = relationship("InformationSource", back_populates="rss_channels")
    category = relationship("Category", back_populates="rss_channels")
