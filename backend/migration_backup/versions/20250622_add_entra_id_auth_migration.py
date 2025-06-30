"""Add entra_id field for Entra External ID migration

Revision ID: 20250622_entra_id
Revises: 5ccfdeebef7a
Create Date: 2025-06-22 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250622_entra_id'
down_revision: Union[str, None] = '5ccfdeebef7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add entra_id field to users table."""
    # Add entra_id column to users table
    op.add_column('users', sa.Column('entra_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_entra_id'), 'users', ['entra_id'], unique=True)


def downgrade() -> None:
    """Remove entra_id field."""
    # Remove the entra_id column and index
    op.drop_index(op.f('ix_users_entra_id'), table_name='users')
    op.drop_column('users', 'entra_id') 