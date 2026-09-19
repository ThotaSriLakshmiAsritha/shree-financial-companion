"""Add onboarding and consent preferences.

Revision ID: 0003_onboarding_preferences
Revises: 0002_identity_auth
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_onboarding_preferences"
down_revision: str | None = "0002_identity_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_preferences", sa.Column("monthly_income_estimate", sa.Numeric(12, 2), nullable=True))
    op.add_column(
        "user_preferences",
        sa.Column("financial_setup_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "user_preferences",
        sa.Column("consent_accepted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("user_preferences", "consent_accepted")
    op.drop_column("user_preferences", "financial_setup_completed")
    op.drop_column("user_preferences", "monthly_income_estimate")

