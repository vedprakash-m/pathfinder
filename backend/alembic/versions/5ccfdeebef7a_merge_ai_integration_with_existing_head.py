"""merge ai integration with existing head

Revision ID: 5ccfdeebef7a
Revises: 20250609_add_ai_integration_tables, 63ee57d6765a
Create Date: 2025-06-09 20:04:56.316971

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5ccfdeebef7a"
down_revision: Union[str, None] = ("20250609_add_ai_integration_tables", "63ee57d6765a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
