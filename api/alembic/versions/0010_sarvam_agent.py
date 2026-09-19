"""Allow Sarvam as a shared voice transport.

Revision ID: 0010_sarvam_agent
Revises: 0009_voice_turn_idempotency
Create Date: 2026-09-19
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0010_sarvam_agent"
down_revision: str | None = "0009_voice_turn_idempotency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("voice_call_sessions", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_voice_call_sessions_provider", type_="check")
        batch_op.create_check_constraint(
            "ck_voice_call_sessions_provider",
            "provider IN ('exotel', 'sarvam')",
        )


def downgrade() -> None:
    with op.batch_alter_table("voice_call_sessions", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_voice_call_sessions_provider", type_="check")
        batch_op.create_check_constraint(
            "ck_voice_call_sessions_provider",
            "provider IN ('exotel')",
        )
