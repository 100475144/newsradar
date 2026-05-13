"""Change category FK on rss_channels from RESTRICT to CASCADE

Revision ID: f9c0d1e2f3a4
Revises: f8b9c0d1e2f3
Create Date: 2026-05-07 10:01:00.000000

Allows deleting categories even when RSS channels reference them.
The test suite (GC-022) needs to delete all categories and recreate them.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f9c0d1e2f3a4"
down_revision: Union[str, Sequence[str], None] = "f8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_rss_channels_category", "rss_channels", type_="foreignkey")
    op.create_foreign_key(
        "fk_rss_channels_category",
        "rss_channels",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_rss_channels_category", "rss_channels", type_="foreignkey")
    op.create_foreign_key(
        "fk_rss_channels_category",
        "rss_channels",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
