"""Create shared voice call sessions for Exotel turns.

Revision ID: 0007_voice_call_sessions
Revises: 0006_educational_state_machine
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_voice_call_sessions"
down_revision: str | None = "0006_educational_state_machine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voice_call_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("external_call_id", sa.String(length=160), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("provider IN ('exotel')", name="ck_voice_call_sessions_provider"),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'failed')",
            name="ck_voice_call_sessions_status",
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id"),
        sa.UniqueConstraint("provider", "external_call_id", name="uq_voice_call_sessions_provider_call"),
    )
    op.create_index("ix_voice_call_sessions_user_id", "voice_call_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_voice_call_sessions_user_id", table_name="voice_call_sessions")
    op.drop_table("voice_call_sessions")
