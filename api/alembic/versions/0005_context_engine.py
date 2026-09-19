"""Create bounded financial, educational, memory, and conversation context tables.

Revision ID: 0005_context_engine
Revises: 0004_financial_domain
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_context_engine"
down_revision: str | None = "0004_financial_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "educational_context",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("concept", sa.String(length=100), nullable=False),
        sa.Column("knowledge_state", sa.String(length=40), nullable=False),
        sa.Column("application_state", sa.String(length=40), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("misconceptions", sa.Text(), nullable=True),
        sa.Column("last_discussed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reinforcement_needed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_educational_context_confidence"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "concept", name="uq_educational_context_user_concept"),
    )
    op.create_index("ix_educational_context_user_id", "educational_context", ["user_id"])

    op.create_table(
        "memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("memory_type", sa.String(length=40), server_default="conversation", nullable=False),
        sa.Column("source", sa.String(length=30), server_default="conversation", nullable=False),
        sa.Column("importance", sa.Numeric(4, 3), server_default="0.5", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("importance >= 0 AND importance <= 1", name="ck_memories_importance"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_user_id", "memories", ["user_id"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "channel IN ('web', 'voice', 'feature_phone')",
            name="ck_conversations_channel",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("intent", sa.String(length=60), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_conversation_messages_role",
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_messages_conversation_id", "conversation_messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_conversation_id", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")
    op.drop_index("ix_educational_context_user_id", table_name="educational_context")
    op.drop_table("educational_context")
