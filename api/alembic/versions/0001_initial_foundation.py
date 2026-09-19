"""Create the initial foundation metadata table.

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_metadata",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "system_metadata",
            sa.column("key", sa.String),
            sa.column("value", sa.String),
        ),
        [{"key": "schema_version", "value": "phase-1"}],
    )


def downgrade() -> None:
    op.drop_table("system_metadata")

