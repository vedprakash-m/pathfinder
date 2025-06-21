"""Add onboarding fields to users table

Revision ID: a1b2c3d4e5f6
Revises: 20250608_add_user_role_field
Create Date: 2025-06-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "a1b2c3d4e5f6"
down_revision = "20250608_add_user_role_field"
branch_labels = None
depends_on = None


def upgrade():
    """Add onboarding fields to users table."""
    # Add onboarding_completed column with default value
    op.add_column(
        "users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, default=False)
    )

    # Add onboarding_completed_at column
    op.add_column(
        "users", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Add onboarding_trip_type column
    op.add_column("users", sa.Column("onboarding_trip_type", sa.String(length=50), nullable=True))


def downgrade():
    """Remove onboarding fields from users table."""
    op.drop_column("users", "onboarding_trip_type")
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_completed")
