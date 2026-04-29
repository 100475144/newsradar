"""Align Notification table with the official API schema

Revision ID: f4d5e6f7a8b9
Revises: f3c4d5e6f7a8
Create Date: 2026-04-30 14:00:00.000000

T6.5 (Phase 1): añade los campos canónicos ``timestamp`` y ``metrics``
a ``notifications``. Los campos internos ``title``, ``message``,
``user_id``, ``news_id`` e ``is_read`` se conservan para la UI.

Backfill: ``timestamp`` se rellena con ``NOW()`` para registros previos
que no tenían columna equivalente, y ``metrics`` queda como array vacío.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "f3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Añadir ``timestamp`` con default NOW() para no romper filas existentes.
    op.add_column(
        "notifications",
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Añadir ``metrics`` JSONB con default vacío.
    op.add_column(
        "notifications",
        sa.Column(
            "metrics",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("notifications", "metrics")
    op.drop_column("notifications", "timestamp")
