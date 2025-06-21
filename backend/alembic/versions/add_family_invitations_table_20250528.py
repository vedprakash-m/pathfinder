"""Add family invitations table

Revision ID: add_family_invitations_table_20250528
Revises: 81a7b1a8b036
Create Date: 2025-05-28 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision: str = "add_family_invitations_table_20250528"
down_revision: Union[str, None] = "81a7b1a8b036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create family_invitations table
    op.create_table(
        "family_invitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("invited_by", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "role", sa.Enum("COORDINATOR", "ADULT", "CHILD", name="familyrole"), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ACCEPTED", "DECLINED", "EXPIRED", name="invitationstatus"),
            nullable=False,
        ),
        sa.Column("invitation_token", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["families.id"],
        ),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invitation_token"),
    )


def downgrade() -> None:
    # Drop family_invitations table
    op.drop_table("family_invitations")
