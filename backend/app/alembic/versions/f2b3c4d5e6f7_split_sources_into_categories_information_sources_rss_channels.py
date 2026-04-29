"""Split sources into categories + information_sources + rss_channels

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-30 10:00:00.000000

T6.3 (Phase 1): Alinea el modelo de fuentes con la API oficial del aula global.

Cambios:
- Se crea la tabla ``categories`` (id, name, source) y se siembran las 17
  categorías IPTC (Media Topics primer nivel) con ``name = code`` para
  preservar compatibilidad con el campo ``sources.category``.
- Se crea la tabla ``information_sources`` (id, name, url). Se backfilea
  agrupando ``sources.medium_name``; la URL se infiere del dominio del
  primer feed de cada medio.
- Se crea la tabla ``rss_channels`` (id, url, category_id, information_source_id,
  name, is_active, ...). Se backfilea copiando filas de ``sources`` con el
  mismo ``id`` para no invalidar las FKs externas (``news.source_id``).
- ``news.source_id`` cambia su FK destino: antes ``sources(id)``, ahora
  ``rss_channels(id)``. Los IDs son idénticos, no hay reasignación de datos.
- Se elimina la tabla ``sources``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 17 IPTC Media Topics primer nivel. ``name`` se almacena como código snake_case
# para que la columna ``sources.category`` (también código) pueda hacer match
# directo en el backfill.
IPTC_CATEGORY_CODES = [
    "arts_culture_entertainment",
    "conflict_war_peace",
    "crime_law_justice",
    "disaster_accident",
    "economy_business_finance",
    "education",
    "environment",
    "health",
    "human_interest",
    "labour",
    "lifestyle_leisure",
    "politics",
    "religion_belief",
    "science_technology",
    "society",
    "sport",
    "weather",
]

# Categoría fallback para canales que no tenían valor en la columna anterior.
FALLBACK_CATEGORY_NAME = "uncategorized"


def upgrade() -> None:
    # 1. Crear categories ────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="IPTC"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )

    # Seed IPTC + categoría fallback (por si quedaban sources sin category).
    for code in IPTC_CATEGORY_CODES + [FALLBACK_CATEGORY_NAME]:
        op.execute(
            sa.text(
                "INSERT INTO categories (name, source) VALUES (:name, 'IPTC') "
                "ON CONFLICT (name) DO NOTHING"
            ).bindparams(name=code)
        )

    # 2. Crear information_sources ───────────────────────────────────
    op.create_table(
        "information_sources",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=120), nullable=False, index=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Backfill information_sources desde sources.medium_name (si existe).
    op.execute(
        sa.text(
            """
            INSERT INTO information_sources (name, url)
            SELECT
                medium_name,
                'https://' || split_part(split_part(MIN(url), '://', 2), '/', 1)
            FROM sources
            WHERE medium_name IS NOT NULL AND medium_name <> ''
            GROUP BY medium_name
            """
        )
    )

    # 3. Crear rss_channels ──────────────────────────────────────────
    op.create_table(
        "rss_channels",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("url", sa.String(length=500), nullable=False, index=True),
        sa.Column("category_id", sa.Integer(), nullable=False, index=True),
        sa.Column("information_source_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="RESTRICT",
            name="fk_rss_channels_category",
        ),
        sa.ForeignKeyConstraint(
            ["information_source_id"],
            ["information_sources.id"],
            ondelete="CASCADE",
            name="fk_rss_channels_information_source",
        ),
        sa.UniqueConstraint("url", name="uq_rss_channels_url"),
    )

    # 4. Backfill rss_channels copiando los IDs de sources tal cual ──
    #    para no invalidar la FK news.source_id.
    op.execute(
        sa.text(
            """
            INSERT INTO rss_channels (
                id, url, category_id, information_source_id, name, is_active,
                created_at, updated_at
            )
            SELECT
                s.id,
                s.url,
                COALESCE(c.id, fb.id) AS category_id,
                isrc.id AS information_source_id,
                s.name,
                s.is_active,
                s.created_at,
                s.updated_at
            FROM sources s
            LEFT JOIN categories c ON c.name = LOWER(COALESCE(s.category, ''))
            LEFT JOIN categories fb ON fb.name = 'uncategorized'
            JOIN information_sources isrc ON isrc.name = s.medium_name
            """
        )
    )

    # Avanzar la sequence para que próximos inserts no choquen con los IDs existentes.
    op.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('rss_channels', 'id'),
                GREATEST((SELECT COALESCE(MAX(id), 0) FROM rss_channels), 1)
            )
            """
        )
    )

    # 5. news.source_id: cambiar FK destino sources → rss_channels ───
    op.drop_constraint("news_source_id_fkey", "news", type_="foreignkey")
    op.create_foreign_key(
        "fk_news_source_id_rss_channels",
        "news",
        "rss_channels",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 6. Eliminar tabla sources ──────────────────────────────────────
    op.drop_table("sources")


def downgrade() -> None:
    # Reversa: recrear sources, copiar de rss_channels (mejor esfuerzo) y
    # restaurar FK de news. Información de medium_name se reconstruye desde
    # information_sources.name.
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medium_name", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("url", name="uq_sources_url"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO sources (id, medium_name, name, url, category, is_active, created_at, updated_at)
            SELECT
                rc.id,
                isrc.name,
                rc.name,
                rc.url,
                c.name,
                rc.is_active,
                rc.created_at,
                rc.updated_at
            FROM rss_channels rc
            JOIN information_sources isrc ON isrc.id = rc.information_source_id
            JOIN categories c ON c.id = rc.category_id
            """
        )
    )

    op.drop_constraint("fk_news_source_id_rss_channels", "news", type_="foreignkey")
    op.create_foreign_key(
        "news_source_id_fkey",
        "news",
        "sources",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_table("rss_channels")
    op.drop_table("information_sources")
    op.drop_table("categories")
