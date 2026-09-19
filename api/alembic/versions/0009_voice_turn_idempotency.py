"""Make voice turn processing idempotent across webhook replays.

Revision ID: 0009_voice_turn_idempotency
Revises: 0008_safety_privacy
Create Date: 2026-09-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_voice_turn_idempotency"
down_revision: str | None = "0008_safety_privacy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voice_turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="processing", nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('processing', 'completed', 'failed')",
            name="ck_voice_turns_status",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["voice_call_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "idempotency_key", name="uq_voice_turns_session_key"),
    )
    op.create_index("ix_voice_turns_session_id", "voice_turns", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_voice_turns_session_id", table_name="voice_turns")
    op.drop_table("voice_turns")
