"""Align User table with the official API schema (T6.7)

Revision ID: f6f7a8b9c0d1
Revises: f5e6f7a8b9c0
Create Date: 2026-04-30 16:00:00.000000

T6.7 (Phase 1): adapta la tabla ``users`` al modelo oficial:
- ``first_name`` y ``last_name`` se amplían a 120 (antes ilimitado).
- ``organization`` pasa a NOT NULL con tope 180. Los registros sin valor
  reciben ``"Unknown"`` en el backfill.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "f5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Backfill: cualquier usuario sin organization recibe ``Unknown``.
    op.execute(
        "UPDATE users SET organization = 'Unknown' "
        "WHERE organization IS NULL OR organization = ''"
    )

    # 2. Cambiar tipos/longitudes y NOT NULL.
    op.alter_column("users", "first_name", type_=sa.String(length=120))
    op.alter_column("users", "last_name", type_=sa.String(length=120))
    op.alter_column(
        "users",
        "organization",
        type_=sa.String(length=180),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "organization",
        type_=sa.String(),
        nullable=True,
    )
    op.alter_column("users", "last_name", type_=sa.String())
    op.alter_column("users", "first_name", type_=sa.String())
