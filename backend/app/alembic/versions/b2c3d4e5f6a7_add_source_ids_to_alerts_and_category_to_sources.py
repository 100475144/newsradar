"""Add source_ids to alerts and category to sources

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add source_ids (JSONB) to alerts
    op.add_column(
        "alerts",
        sa.Column("source_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute("UPDATE alerts SET source_ids = '[]'::jsonb WHERE source_ids IS NULL")
    op.alter_column("alerts", "source_ids", nullable=False)

    # Add category to sources
    op.add_column(
        "sources",
        sa.Column("category", sa.String(length=255), nullable=True),
    )
    op.create_index(op.f('ix_sources_category'), 'sources', ['category'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sources_category'), table_name='sources')
    op.drop_column("sources", "category")
    op.drop_column("alerts", "source_ids")
