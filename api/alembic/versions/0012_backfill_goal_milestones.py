"""Backfill default milestones for goals created before multi-goal support.

Revision ID: 0012_backfill_goal_milestones
Revises: 0011_multiple_savings_goals
Create Date: 2026-09-19
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0012_backfill_goal_milestones"
down_revision: str | None = "0011_multiple_savings_goals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO goal_milestones (id, goal_id, amount, title)
        SELECT gen_random_uuid(), g.id, round(g.target_amount * milestone.ratio, 2), milestone.title
        FROM goals g
        CROSS JOIN (VALUES
            (0.25::numeric, '25% milestone'),
            (0.50::numeric, '50% milestone'),
            (0.75::numeric, '75% milestone'),
            (1.00::numeric, 'Goal completed')
        ) AS milestone(ratio, title)
        WHERE NOT EXISTS (
            SELECT 1 FROM goal_milestones existing WHERE existing.goal_id = g.id
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM goal_milestones
        WHERE title IN ('25% milestone', '50% milestone', '75% milestone', 'Goal completed')
        """
    )
