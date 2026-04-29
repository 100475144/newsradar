"""Create stats table (T6.6)

Revision ID: f5e6f7a8b9c0
Revises: f4d5e6f7a8b9
Create Date: 2026-04-30 15:00:00.000000

T6.6 (Phase 1): tabla ``stats`` exigida por la API oficial. Almacena
snapshots con un array de métricas (``{name, value}``).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "f4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stats",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "metrics",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Quitar server_default tras crear, para que el ORM gobierne metricas.
    op.alter_column("stats", "metrics", server_default=None)


def downgrade() -> None:
    op.drop_table("stats")
