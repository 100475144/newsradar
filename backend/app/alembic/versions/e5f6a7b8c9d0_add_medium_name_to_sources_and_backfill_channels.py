"""Add medium_name to sources and backfill existing channel names

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-19 19:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("medium_name", sa.String(length=120), nullable=True),
    )
    op.create_index(op.f("ix_sources_medium_name"), "sources", ["medium_name"], unique=False)

    op.execute(
        """
        UPDATE sources
        SET medium_name = CASE
                WHEN position(' - ' in name) > 0 THEN btrim(split_part(name, ' - ', 1))
                ELSE btrim(name)
            END,
            name = CASE
                WHEN position(' - ' in name) > 0 THEN btrim(substring(name FROM position(' - ' in name) + 3))
                ELSE btrim(name)
            END
        WHERE medium_name IS NULL
        """
    )

    op.alter_column("sources", "medium_name", nullable=False)


def downgrade() -> None:
    op.execute(
        """
        UPDATE sources
        SET name = CASE
                WHEN medium_name IS NOT NULL
                     AND btrim(medium_name) <> ''
                     AND medium_name <> name
                THEN medium_name || ' - ' || name
                ELSE name
            END
        """
    )
    op.drop_index(op.f("ix_sources_medium_name"), table_name="sources")
    op.drop_column("sources", "medium_name")
