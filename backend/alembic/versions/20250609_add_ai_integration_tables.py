"""Add AI integration tables for Pathfinder Assistant and Magic Polls

Revision ID: 20250609_add_ai_integration_tables
Revises: a1b2c3d4e5f6
Create Date: 2025-06-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250609_add_ai_integration_tables"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Assistant interactions table
    op.create_table(
        "assistant_interactions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("trip_id", sa.String(), nullable=True),
        sa.Column("family_id", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context_type", sa.String(50), nullable=False),
        sa.Column("response_data", sa.JSON(), nullable=True),
        sa.Column("response_cards", sa.JSON(), nullable=True),
        sa.Column("suggestions", sa.JSON(), nullable=True),
        sa.Column("feedback_rating", sa.Integer(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Magic polls table
    op.create_table(
        "magic_polls",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("trip_id", sa.String(), nullable=False),
        sa.Column("creator_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("poll_type", sa.String(50), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("responses", sa.JSON(), nullable=True),
        sa.Column("ai_analysis", sa.JSON(), nullable=True),
        sa.Column("consensus_recommendation", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # AI response cards table (for rich structured responses)
    op.create_table(
        "ai_response_cards",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("interaction_id", sa.String(), nullable=False),
        sa.Column("card_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # AI suggestions table (for contextual suggestions)
    op.create_table(
        "ai_suggestions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("trip_id", sa.String(), nullable=True),
        sa.Column("suggestion_type", sa.String(50), nullable=False),
        sa.Column("context", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("action_data", sa.JSON(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, default=5),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, default=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index("idx_assistant_interactions_user_id", "assistant_interactions", ["user_id"])
    op.create_index("idx_assistant_interactions_trip_id", "assistant_interactions", ["trip_id"])
    op.create_index(
        "idx_assistant_interactions_created_at", "assistant_interactions", ["created_at"]
    )

    op.create_index("idx_magic_polls_trip_id", "magic_polls", ["trip_id"])
    op.create_index("idx_magic_polls_creator_id", "magic_polls", ["creator_id"])
    op.create_index("idx_magic_polls_status", "magic_polls", ["status"])

    op.create_index("idx_ai_response_cards_interaction_id", "ai_response_cards", ["interaction_id"])
    op.create_index("idx_ai_response_cards_card_type", "ai_response_cards", ["card_type"])

    op.create_index("idx_ai_suggestions_user_id", "ai_suggestions", ["user_id"])
    op.create_index("idx_ai_suggestions_trip_id", "ai_suggestions", ["trip_id"])
    op.create_index("idx_ai_suggestions_context", "ai_suggestions", ["context"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_ai_suggestions_context")
    op.drop_index("idx_ai_suggestions_trip_id")
    op.drop_index("idx_ai_suggestions_user_id")
    op.drop_index("idx_ai_response_cards_card_type")
    op.drop_index("idx_ai_response_cards_interaction_id")
    op.drop_index("idx_magic_polls_status")
    op.drop_index("idx_magic_polls_creator_id")
    op.drop_index("idx_magic_polls_trip_id")
    op.drop_index("idx_assistant_interactions_created_at")
    op.drop_index("idx_assistant_interactions_trip_id")
    op.drop_index("idx_assistant_interactions_user_id")

    # Drop tables
    op.drop_table("ai_suggestions")
    op.drop_table("ai_response_cards")
    op.drop_table("magic_polls")
    op.drop_table("assistant_interactions")
