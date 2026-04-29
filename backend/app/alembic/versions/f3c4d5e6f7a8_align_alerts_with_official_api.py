"""Align Alert table with the official API schema

Revision ID: f3c4d5e6f7a8
Revises: f2b3c4d5e6f7
Create Date: 2026-04-30 12:00:00.000000

T6.4 (Phase 1): adapta el modelo Alert al ``main.py`` oficial.

- ``expanded_keywords`` → ``descriptors``.
- ``category`` (string) → ``categories`` (JSONB de objetos {code, label}).
- ``source_ids`` (JSONB int) → ``rss_channels_ids`` (JSONB string) +
  ``information_sources_ids`` (JSONB string, vacío en backfill).
- ``created_by`` → ``user_id``.
- Se relaja ``keyword`` a NULL (campo interno, ya no es obligatorio).
- ``cron_expression`` se amplía a 120 caracteres.

Campos internos mantenidos: ``keyword``, ``is_active``, ``notify_in_app``,
``notify_email``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "f2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Renombres directos.
    op.alter_column("alerts", "expanded_keywords", new_column_name="descriptors")
    op.alter_column("alerts", "created_by", new_column_name="user_id")

    # 2. Aliviar `keyword` (ahora opcional).
    op.alter_column("alerts", "keyword", nullable=True, type_=sa.String(length=200))

    # 3. Ampliar cron_expression a 120 caracteres.
    op.alter_column("alerts", "cron_expression", type_=sa.String(length=120))

    # 4. Ampliar `name` a 200.
    op.alter_column("alerts", "name", type_=sa.String(length=200))

    # 5. Añadir columnas nuevas (con default vacío).
    op.add_column(
        "alerts",
        sa.Column(
            "categories",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "alerts",
        sa.Column(
            "rss_channels_ids",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "alerts",
        sa.Column(
            "information_sources_ids",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # 6. Backfill: category (string) → categories (array de un objeto).
    op.execute(
        sa.text(
            """
            UPDATE alerts
               SET categories = jsonb_build_array(
                       jsonb_build_object('code', category, 'label', category)
                   )
             WHERE category IS NOT NULL AND category <> ''
            """
        )
    )

    # 7. Backfill: source_ids (jsonb int[]) → rss_channels_ids (jsonb str[]).
    op.execute(
        sa.text(
            """
            UPDATE alerts
               SET rss_channels_ids = COALESCE(
                       (
                           SELECT jsonb_agg(to_jsonb(value::text))
                             FROM jsonb_array_elements_text(source_ids) AS value
                       ),
                       '[]'::jsonb
                   )
             WHERE source_ids IS NOT NULL
            """
        )
    )

    # 8. Eliminar columnas viejas.
    op.drop_column("alerts", "source_ids")
    op.drop_column("alerts", "category")

    # Quitar server_defaults para que ORM gobierne valores futuros.
    op.alter_column("alerts", "categories", server_default=None)
    op.alter_column("alerts", "rss_channels_ids", server_default=None)
    op.alter_column("alerts", "information_sources_ids", server_default=None)


def downgrade() -> None:
    # Reañadir columnas viejas y restaurar datos a partir de las nuevas.
    op.add_column(
        "alerts",
        sa.Column(
            "category",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "alerts",
        sa.Column(
            "source_ids",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE alerts
               SET category = COALESCE(
                       (categories->0->>'code'),
                       NULL
                   )
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE alerts
               SET source_ids = COALESCE(
                       (
                           SELECT jsonb_agg((value::text)::int)
                             FROM jsonb_array_elements_text(rss_channels_ids) AS value
                       ),
                       '[]'::jsonb
                   )
            """
        )
    )

    op.drop_column("alerts", "information_sources_ids")
    op.drop_column("alerts", "rss_channels_ids")
    op.drop_column("alerts", "categories")

    op.alter_column("alerts", "name", type_=sa.String(length=255))
    op.alter_column("alerts", "cron_expression", type_=sa.String(length=100))
    op.alter_column("alerts", "keyword", nullable=False, type_=sa.String(length=255))
    op.alter_column("alerts", "user_id", new_column_name="created_by")
    op.alter_column("alerts", "descriptors", new_column_name="expanded_keywords")
