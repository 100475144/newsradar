"""Add classification_origin to news

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-04-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "news",
        sa.Column(
            "classification_origin",
            sa.String(length=20),
            nullable=True,
            server_default="unknown",
        ),
    )
    op.create_index(
        op.f("ix_news_classification_origin"),
        "news",
        ["classification_origin"],
        unique=False,
    )

    op.execute(
        """
        UPDATE news
        SET classification_origin = 'unknown'
        WHERE category IS NULL OR btrim(category) = ''
        """
    )

    op.execute(
        """
        UPDATE news AS n
        SET classification_origin = CASE
            WHEN s.category IS NOT NULL AND btrim(s.category) <> '' AND n.category = s.category THEN 'source'
            ELSE 'rss'
        END
        FROM sources AS s
        WHERE n.source_id = s.id
          AND n.category IS NOT NULL
          AND btrim(n.category) <> ''
        """
    )

    op.execute(
        """
        UPDATE news
        SET classification_origin = 'rss'
        WHERE source_id IS NULL
          AND category IS NOT NULL
          AND btrim(category) <> ''
        """
    )

    op.alter_column(
        "news",
        "classification_origin",
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_news_classification_origin"), table_name="news")
    op.drop_column("news", "classification_origin")
