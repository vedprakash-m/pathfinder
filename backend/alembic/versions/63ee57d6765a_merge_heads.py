"""merge heads

Revision ID: 63ee57d6765a
Revises: a1b2c3d4e5f6, e4171dc63af8
Create Date: 2025-06-08 20:13:13.592599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63ee57d6765a'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'e4171dc63af8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
