"""Add user role field

Revision ID: 20250608_add_user_role_field
Revises: add_family_invitations_table_20250528
Create Date: 2025-06-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20250608_add_user_role_field"
down_revision: Union[str, None] = "add_family_invitations_table_20250528"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to users table with default FAMILY_ADMIN
    # SQLite doesn't support ENUMs or adding constraints after table creation
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="family_admin"),
    )


def downgrade() -> None:
    # Remove role column from users table
    op.drop_column("users", "role")
