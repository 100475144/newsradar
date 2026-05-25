"""Add phone column to users

Revision ID: a7b8c9d0e1f2
Revises: f4d5e6f7a8b9
Create Date: 2026-05-25 11:26:00.000000

Add a new phone column (string, 9 digits) to the users table. DB column is nullable
so existing rows are not broken; API enforces presence/format.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f9c0d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add phone column: VARCHAR(9), nullable
    op.add_column(
        "users",
        sa.Column("phone", sa.String(length=9), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "phone")
