from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context.schemas import ActiveGoalContext, FinancialContextSlice
from app.financial.models import FinancialContext, Goal


def build_financial_context(db: Session, user_id: UUID) -> FinancialContextSlice:
    """Return only the small financial summary needed by the conversation layer."""
    context = db.get(FinancialContext, user_id)
    active_goal = db.scalar(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.status == "active")
        .order_by(Goal.created_at.desc())
        .limit(1)
    )

    return FinancialContextSlice(
        income_pattern=context.income_pattern if context else None,
        current_savings=context.current_savings if context else Decimal(0),
        active_goal=(
            ActiveGoalContext(
                name=active_goal.name,
                target_amount=active_goal.target_amount,
                current_amount=active_goal.current_amount,
                currency=active_goal.currency,
                target_date=active_goal.target_date.isoformat() if active_goal.target_date else None,
            )
            if active_goal
            else None
        ),
    )
