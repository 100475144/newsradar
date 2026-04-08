"""create news table

Revision ID: 7515cb2144f0
Revises: cd786bdde698
Create Date: 2026-04-08 16:04:36.847387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7515cb2144f0'
down_revision: Union[str, Sequence[str], None] = 'cd786bdde698'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("link", sa.String(length=1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_news_content_hash"),
    )

    op.create_index(op.f("ix_news_id"), "news", ["id"], unique=False)
    op.create_index(op.f("ix_news_source_id"), "news", ["source_id"], unique=False)
    op.create_index(op.f("ix_news_link"), "news", ["link"], unique=False)
    op.create_index(op.f("ix_news_category"), "news", ["category"], unique=False)
    op.create_index(op.f("ix_news_external_id"), "news", ["external_id"], unique=False)
    op.create_index(op.f("ix_news_content_hash"), "news", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_news_content_hash"), table_name="news")
    op.drop_index(op.f("ix_news_external_id"), table_name="news")
    op.drop_index(op.f("ix_news_category"), table_name="news")
    op.drop_index(op.f("ix_news_link"), table_name="news")
    op.drop_index(op.f("ix_news_source_id"), table_name="news")
    op.drop_index(op.f("ix_news_id"), table_name="news")
    op.drop_table("news")