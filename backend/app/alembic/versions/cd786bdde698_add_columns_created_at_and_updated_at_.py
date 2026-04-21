"""Add columns created_at and updated_at in sources table

Revision ID: cd786bdde698
Revises: 567e56f08b73
Create Date: 2026-04-07 14:45:42.959428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd786bdde698'
down_revision: Union[str, Sequence[str], None] = '567e56f08b73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sources',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.add_column(
        'sources',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sources', 'updated_at')
    op.drop_column('sources', 'created_at')
    # ### end Alembic commands ###
