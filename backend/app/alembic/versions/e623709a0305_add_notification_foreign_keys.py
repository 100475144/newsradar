"""add notification foreign keys

Revision ID: e623709a0305
Revises: f6a7b8c9d0e1
Create Date: 2026-04-21 00:10:57.944386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e623709a0305'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_notifications_alert_id_alerts",
        "notifications",
        "alerts",
        ["alert_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notifications_news_id_news",
        "notifications",
        "news",
        ["news_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_notifications_news_id_news",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_notifications_alert_id_alerts",
        "notifications",
        type_="foreignkey",
    )