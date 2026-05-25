"""Add priority column to alerts

Revision ID: g7h8i9j0k1l2
Revises: a7b8c9d0e1f2
Create Date: 2026-05-25 12:00:00.000000

Add priority column to alerts table (INTEGER, 1-3 range).
1=red (high), 2=yellow (medium), 3=green (low).
Default value is 2 (medium priority).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add priority column: INTEGER, default 2, not null
    op.add_column(
        "alerts",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="2"),
    )


def downgrade() -> None:
    op.drop_column("alerts", "priority")
