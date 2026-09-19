"""Add independent savings goals, milestones, and contributions.

Revision ID: 0011_multiple_savings_goals
Revises: 0010_sarvam_agent
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0011_multiple_savings_goals"
down_revision: str | None = "0010_sarvam_agent"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("goals", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("goals", sa.Column("category", sa.String(length=40), server_default="general", nullable=False))
    op.add_column("goals", sa.Column("icon", sa.String(length=20), server_default="✦", nullable=False))

    op.create_table(
        "goal_milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_goal_milestones_amount"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goal_milestones_goal_id", "goal_milestones", ["goal_id"])

    op.create_table(
        "goal_contributions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("contributed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_goal_contributions_amount"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index("ix_goal_contributions_goal_id", "goal_contributions", ["goal_id"])
    op.create_index("ix_goal_contributions_user_id", "goal_contributions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_goal_contributions_user_id", table_name="goal_contributions")
    op.drop_index("ix_goal_contributions_goal_id", table_name="goal_contributions")
    op.drop_table("goal_contributions")
    op.drop_index("ix_goal_milestones_goal_id", table_name="goal_milestones")
    op.drop_table("goal_milestones")
    op.drop_column("goals", "icon")
    op.drop_column("goals", "category")
    op.drop_column("goals", "description")
