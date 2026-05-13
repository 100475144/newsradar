"""Make notification news_id nullable

Revision ID: f8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-05-07 10:00:00.000000

The model declares news_id as nullable=True but the original migration
created the column as NOT NULL. This fix aligns the DB with the model
so that API-created notifications (without a news article) can set
news_id=NULL.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique constraint that includes news_id first,
    # then recreate it to allow NULL news_id properly.
    op.alter_column(
        "notifications",
        "news_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # Delete rows with NULL news_id before making it NOT NULL again.
    op.execute("DELETE FROM notifications WHERE news_id IS NULL")
    op.alter_column(
        "notifications",
        "news_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
