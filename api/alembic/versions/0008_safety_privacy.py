"""Add privacy consent metadata and the server-side audit trail.

Revision ID: 0008_safety_privacy
Revises: 0007_voice_call_sessions
Create Date: 2026-09-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_safety_privacy"
down_revision: str | None = "0007_voice_call_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_preferences", sa.Column("consent_version", sa.String(length=40), nullable=True))
    op.add_column("user_preferences", sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("channel", sa.String(length=30), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_user_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_column("user_preferences", "consent_at")
    op.drop_column("user_preferences", "consent_version")
