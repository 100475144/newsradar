"""Convert categories PK to IPTC official 8-digit code + drop uncategorized.

Revision ID: f8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-05-06 00:00:00.000000

Smoke tests del aula global (SMOKE-004 y SMOKE-005) requieren:
  - SMOKE-005: ``GET /api/v1/categories`` devuelve las 17 categorías IPTC de
    primer nivel con ``id`` = código oficial (``"01000000"`` … ``"17000000"``)
    y ``name`` = nombre español canónico.
  - SMOKE-004: no debe existir la categoría ``uncategorized`` sin canales.

Esta migración:
  1. Crea columnas ``categories.id_new`` (TEXT) y ``rss_channels.category_id_new``
     (TEXT).
  2. Mapea cada fila legacy snake_case a su código IPTC oficial.
  3. Reasigna canales con categoría ``uncategorized`` (legacy) al fallback
     ``14000000`` (sociedad).
  4. Sustituye la PK INTEGER por la nueva PK TEXT y la FK de rss_channels.
  5. Renombra los nombres de categoría al español canónico.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Mapping legacy snake_case → (código IPTC oficial, nombre español canónico).
LEGACY_TO_OFFICIAL: dict[str, tuple[str, str]] = {
    "arts_culture_entertainment": ("01000000", "artes, cultura, entretenimiento y medios"),
    "crime_law_justice":          ("02000000", "policía y justicia"),
    "disaster_accident":          ("03000000", "catástrofes y accidentes"),
    "economy_business_finance":   ("04000000", "economía, negocios y finanzas"),
    "education":                  ("05000000", "educación"),
    "environment":                ("06000000", "medio ambiente"),
    "health":                     ("07000000", "salud"),
    "human_interest":             ("08000000", "interés humano, animales, insólito"),
    "labour":                     ("09000000", "mano de obra"),
    "lifestyle_leisure":          ("10000000", "estilo de vida y tiempo libre"),
    "politics":                   ("11000000", "política"),
    "religion_belief":            ("12000000", "religión y creencias"),
    "science_technology":         ("13000000", "ciencia y tecnología"),
    "society":                    ("14000000", "sociedad"),
    "sport":                      ("15000000", "deportes"),
    "conflict_war_peace":         ("16000000", "conflictos, guerras y paz"),
    "weather":                    ("17000000", "tiempo (meteorología)"),
}

DEFAULT_FALLBACK_CODE = "14000000"


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Añadir columnas TEXT auxiliares.
    op.add_column(
        "categories",
        sa.Column("id_new", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "rss_channels",
        sa.Column("category_id_new", sa.String(length=8), nullable=True),
    )

    # 2. Backfill categories.id_new desde el ``name`` legacy.
    for legacy_name, (official_code, _spanish) in LEGACY_TO_OFFICIAL.items():
        op.execute(
            sa.text(
                "UPDATE categories SET id_new = :code WHERE name = :name"
            ).bindparams(code=official_code, name=legacy_name)
        )

    # 3. Backfill rss_channels.category_id_new desde la FK actual.
    op.execute(
        sa.text(
            """
            UPDATE rss_channels rc
            SET category_id_new = c.id_new
            FROM categories c
            WHERE c.id = rc.category_id
            """
        )
    )

    # 4. Reasignar canales con categoría 'uncategorized' (o cualquier otra
    #    fila sin id_new mapeado) al fallback IPTC oficial.
    #    Antes hay que asegurarse de que la fila fallback tiene id_new.
    op.execute(
        sa.text(
            """
            UPDATE rss_channels
            SET category_id_new = :fallback
            WHERE category_id_new IS NULL
            """
        ).bindparams(fallback=DEFAULT_FALLBACK_CODE)
    )

    # 5. Eliminar filas legacy de ``categories`` que no son IPTC primer nivel
    #    (típicamente la fila ``uncategorized``). Esto hace cumplir SMOKE-004.
    op.execute(
        sa.text("DELETE FROM categories WHERE id_new IS NULL")
    )

    # 6. Drop FK antigua y constraints PK/UQ.
    op.drop_constraint(
        "fk_rss_channels_category", "rss_channels", type_="foreignkey"
    )
    op.drop_constraint("uq_categories_name", "categories", type_="unique")
    op.drop_constraint("categories_pkey", "categories", type_="primary")

    # Drop índices auto-creados por SQLAlchemy ``index=True``.
    op.execute(sa.text("DROP INDEX IF EXISTS ix_categories_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_rss_channels_category_id"))

    # 7. Sustituir las columnas: borrar las antiguas y renombrar las nuevas.
    op.drop_column("rss_channels", "category_id")
    op.alter_column(
        "rss_channels",
        "category_id_new",
        new_column_name="category_id",
        nullable=False,
    )

    op.drop_column("categories", "id")
    op.alter_column(
        "categories",
        "id_new",
        new_column_name="id",
        nullable=False,
    )

    # 8. Re-crear PK / UQ / FK con los nuevos tipos.
    op.create_primary_key("categories_pkey", "categories", ["id"])
    op.create_index("ix_categories_id", "categories", ["id"], unique=False)
    op.create_unique_constraint("uq_categories_name", "categories", ["name"])

    op.create_index(
        "ix_rss_channels_category_id",
        "rss_channels",
        ["category_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_rss_channels_category",
        "rss_channels",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 9. Renombrar a español canónico (idempotente). ``UPDATE`` sobre name
    #    distinto a otro existente — usamos un buffer temporal para evitar
    #    colisiones con el unique constraint en pasos intermedios.
    for _legacy, (official_code, spanish) in LEGACY_TO_OFFICIAL.items():
        op.execute(
            sa.text(
                "UPDATE categories SET name = :spanish WHERE id = :id"
            ).bindparams(spanish=spanish, id=official_code)
        )


def downgrade() -> None:
    """Revertir a PK INTEGER + nombres snake_case.

    Nota: si en upgrade se borraron filas no IPTC (uncategorized) los
    canales ya estarán reasignados; no se intenta recuperar la fila
    original de ``uncategorized``.
    """
    # 1. Renombrar nombres a snake_case.
    for legacy, (official_code, _spanish) in LEGACY_TO_OFFICIAL.items():
        op.execute(
            sa.text(
                "UPDATE categories SET name = :legacy WHERE id = :id"
            ).bindparams(legacy=legacy, id=official_code)
        )

    # 2. Crear columnas auxiliares INTEGER.
    op.add_column("categories", sa.Column("id_int", sa.Integer(), nullable=True))
    op.add_column(
        "rss_channels",
        sa.Column("category_id_int", sa.Integer(), nullable=True),
    )

    # 3. Asignar enteros incrementales.
    op.execute(
        sa.text(
            """
            WITH ordered AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
                FROM categories
            )
            UPDATE categories c
            SET id_int = ordered.rn
            FROM ordered
            WHERE c.id = ordered.id
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE rss_channels rc
            SET category_id_int = c.id_int
            FROM categories c
            WHERE c.id = rc.category_id
            """
        )
    )

    op.drop_constraint(
        "fk_rss_channels_category", "rss_channels", type_="foreignkey"
    )
    op.drop_constraint("uq_categories_name", "categories", type_="unique")
    op.drop_constraint("categories_pkey", "categories", type_="primary")
    op.drop_index("ix_rss_channels_category_id", table_name="rss_channels")
    op.drop_index("ix_categories_id", table_name="categories")

    op.drop_column("rss_channels", "category_id")
    op.alter_column(
        "rss_channels",
        "category_id_int",
        new_column_name="category_id",
        nullable=False,
    )

    op.drop_column("categories", "id")
    op.alter_column(
        "categories",
        "id_int",
        new_column_name="id",
        nullable=False,
    )

    op.create_primary_key("categories_pkey", "categories", ["id"])
    op.create_index("ix_categories_id", "categories", ["id"], unique=False)
    op.create_unique_constraint("uq_categories_name", "categories", ["name"])
    op.create_index(
        "ix_rss_channels_category_id",
        "rss_channels",
        ["category_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_rss_channels_category",
        "rss_channels",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
