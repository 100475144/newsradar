"""test

Revision ID: 9fb7e775ba22
Revises: c1f96429ba06
Create Date: 2026-04-01 16:20:17.475742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fb7e775ba22'
down_revision: Union[str, Sequence[str], None] = 'c1f96429ba06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
