"""Create the financial domain and transaction proposal workflow.

Revision ID: 0004_financial_domain
Revises: 0003_onboarding_preferences
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_financial_domain"
down_revision: str | None = "0003_onboarding_preferences"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_context",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("income_pattern", sa.String(length=40), nullable=True),
        sa.Column("monthly_income_estimate", sa.Numeric(12, 2), nullable=True),
        sa.Column("current_savings", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("total_income", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("total_expenses", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("total_savings", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("last_financial_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "income_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("income_type", sa.String(length=40), nullable=False),
        sa.Column("typical_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("frequency", sa.String(length=30), nullable=True),
        sa.Column("seasonal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("typical_amount >= 0", name="ck_income_sources_typical_amount"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_income_sources_user_id", "income_sources", ["user_id"])
    op.create_table(
        "financial_obligations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("frequency", sa.String(length=30), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(length=20), server_default="normal", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_financial_obligations_amount"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_obligations_user_id", "financial_obligations", ["user_id"])
    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(14, 2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("target_amount > 0", name="ck_goals_target_amount"),
        sa.CheckConstraint("current_amount >= 0", name="ck_goals_current_amount"),
        sa.CheckConstraint("status IN ('active', 'completed', 'paused')", name="ck_goals_status"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])
    op.create_table(
        "transaction_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), server_default="0", nullable=False),
        sa.Column("raw_statement", sa.Text(), nullable=True),
        sa.Column("goal_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_transaction_proposals_amount"),
        sa.CheckConstraint(
            "transaction_type IN ('income', 'expense', 'saving')",
            name="ck_transaction_proposals_type",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_transaction_proposals_confidence",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected')",
            name="ck_transaction_proposals_status",
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transaction_proposals_user_id", "transaction_proposals", ["user_id"])
    op.create_index("ix_transaction_proposals_goal_id", "transaction_proposals", ["goal_id"])
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("confirmation_status", sa.String(length=20), server_default="confirmed", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount"),
        sa.CheckConstraint("transaction_type IN ('income', 'expense', 'saving')", name="ck_transactions_type"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_transactions_confidence"),
        sa.CheckConstraint(
            "confirmation_status IN ('pending', 'confirmed', 'rejected')",
            name="ck_transactions_confirmation_status",
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proposal_id"], ["transaction_proposals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("proposal_id"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_goal_id", "transactions", ["goal_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_goal_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_transaction_proposals_goal_id", table_name="transaction_proposals")
    op.drop_index("ix_transaction_proposals_user_id", table_name="transaction_proposals")
    op.drop_table("transaction_proposals")
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_table("goals")
    op.drop_index("ix_financial_obligations_user_id", table_name="financial_obligations")
    op.drop_table("financial_obligations")
    op.drop_index("ix_income_sources_user_id", table_name="income_sources")
    op.drop_table("income_sources")
    op.drop_table("financial_context")

