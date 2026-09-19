from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import Profile
from app.core.time import local_today
from app.financial.models import (
    FinancialContext,
    FinancialObligation,
    Goal,
    GoalContribution,
    GoalMilestone,
    IncomeSource,
    Transaction,
    TransactionProposal,
)
from app.financial.schemas import (
    GoalCreate,
    SavingsDistributionCreate,
    IncomeSourceCreate,
    ObligationCreate,
    TransactionProposalCreate,
)


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def ensure_financial_context(db: Session, user_id: UUID) -> FinancialContext:
    context = db.get(FinancialContext, user_id)
    if context is None:
        if db.get(Profile, user_id) is None:
            raise _not_found("Profile not found.")
        context = FinancialContext(user_id=user_id)
        db.add(context)
        db.flush()
    return context


def _recalculate_current_savings(context: FinancialContext) -> None:
    """Keep available savings consistent with income, expenses, and explicit savings."""
    context.current_savings = max(context.total_income - context.total_expenses, Decimal("0")) + context.total_savings


def _sync_unallocated_goal_progress(db: Session, user_id: UUID, context: FinancialContext) -> bool:
    """Apply net income to an untouched active goal used by the dashboard.

    The web experience currently records income and expenses, while explicit
    goal allocations are represented by saving transactions. Do not overwrite
    a goal that already has an explicit amount; only reconcile a zero-valued
    active goal from the user's net financial position.
    """
    active_goals = list(
        db.scalars(
            select(Goal)
            .where(Goal.user_id == user_id, Goal.status == "active")
            .order_by(Goal.created_at.desc())
        )
    )
    if len(active_goals) != 1:
        return False
    goal = active_goals[0]
    has_explicit_contribution = db.scalar(
        select(GoalContribution.id).where(GoalContribution.goal_id == goal.id).limit(1)
    ) is not None
    if has_explicit_contribution:
        return False

    progress = min(context.current_savings, goal.target_amount)
    changed = progress != goal.current_amount
    goal.current_amount = progress
    if progress >= goal.target_amount:
        goal.status = "completed"
    milestones_changed = _update_goal_milestones(db, goal, datetime.now(timezone.utc))
    return changed or milestones_changed


def _default_milestones(target_amount: Decimal) -> list[tuple[Decimal, str]]:
    return [
        (target_amount * Decimal("0.25"), "25% milestone"),
        (target_amount * Decimal("0.50"), "50% milestone"),
        (target_amount * Decimal("0.75"), "75% milestone"),
        (target_amount, "Goal completed"),
    ]


def _update_goal_milestones(db: Session, goal: Goal, now: datetime) -> bool:
    changed = False
    for milestone in goal.milestones:
        if not milestone.is_completed and goal.current_amount >= milestone.amount:
            milestone.is_completed = True
            milestone.completed_at = now
            changed = True
    return changed


def create_transaction_proposal(
    db: Session,
    user_id: UUID,
    payload: TransactionProposalCreate,
) -> TransactionProposal:
    if payload.goal_id is not None:
        goal = db.scalar(select(Goal).where(Goal.id == payload.goal_id, Goal.user_id == user_id))
        if goal is None:
            raise _not_found("Goal not found for this user.")
        if payload.transaction_type != "saving":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only saving proposals can be attached to a goal.",
            )

    proposal = TransactionProposal(
        user_id=user_id,
        transaction_type=payload.transaction_type,
        amount=payload.amount,
        currency=payload.currency,
        category=payload.category,
        description=payload.description,
        transaction_date=payload.date,
        source=payload.source,
        confidence=payload.confidence,
        raw_statement=payload.raw_statement,
        goal_id=payload.goal_id,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def list_transaction_proposals(db: Session, user_id: UUID, pending_only: bool = False) -> list[TransactionProposal]:
    statement = select(TransactionProposal).where(TransactionProposal.user_id == user_id)
    if pending_only:
        statement = statement.where(TransactionProposal.status == "pending")
    return list(db.scalars(statement.order_by(TransactionProposal.created_at.desc())))


def confirm_transaction_proposal(
    db: Session,
    user_id: UUID,
    proposal_id: UUID,
) -> Transaction:
    proposal = db.scalar(
        select(TransactionProposal).where(
            TransactionProposal.id == proposal_id,
            TransactionProposal.user_id == user_id,
        )
    )
    if proposal is None:
        raise _not_found("Transaction proposal not found.")
    if proposal.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a pending proposal can be confirmed.",
        )

    now = datetime.now(timezone.utc)
    context = ensure_financial_context(db, user_id)
    goal = None
    if proposal.transaction_type == "saving" and proposal.goal_id is not None:
        goal = db.scalar(select(Goal).where(Goal.id == proposal.goal_id, Goal.user_id == user_id))
        if goal is None:
            raise _not_found("Goal not found for this user.")
        if goal.status != "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active goals can receive contributions.")
        remaining = max(goal.target_amount - goal.current_amount, Decimal("0"))
        if proposal.amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Contribution exceeds the remaining goal amount of {remaining}.",
            )
    transaction = Transaction(
        user_id=user_id,
        proposal_id=proposal.id,
        transaction_type=proposal.transaction_type,
        amount=proposal.amount,
        currency=proposal.currency,
        category=proposal.category,
        description=proposal.description,
        transaction_date=proposal.transaction_date,
        source=proposal.source,
        confidence=proposal.confidence,
        confirmation_status="confirmed",
        confirmed_at=now,
        goal_id=proposal.goal_id,
    )
    db.add(transaction)

    if proposal.transaction_type == "income":
        context.total_income += proposal.amount
    elif proposal.transaction_type == "expense":
        context.total_expenses += proposal.amount
    else:
        context.total_savings += proposal.amount
        context.current_savings += proposal.amount
        if goal is not None:
            goal.current_amount += proposal.amount
            if goal.current_amount >= goal.target_amount:
                goal.status = "completed"
            _update_goal_milestones(db, goal, now)

    _recalculate_current_savings(context)

    if proposal.transaction_type in {"income", "expense"}:
        _sync_unallocated_goal_progress(db, user_id, context)

    context.last_financial_update = now
    proposal.status = "confirmed"
    proposal.confirmed_at = now
    db.flush()
    if goal is not None:
        db.add(
            GoalContribution(
                goal_id=goal.id,
                user_id=user_id,
                amount=proposal.amount,
                transaction_id=transaction.id,
                contributed_at=now,
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This proposal has already been confirmed.",
        ) from exc
    db.refresh(transaction)
    return transaction


def reject_transaction_proposal(db: Session, user_id: UUID, proposal_id: UUID) -> TransactionProposal:
    proposal = db.scalar(
        select(TransactionProposal).where(
            TransactionProposal.id == proposal_id,
            TransactionProposal.user_id == user_id,
        )
    )
    if proposal is None:
        raise _not_found("Transaction proposal not found.")
    if proposal.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a pending proposal can be rejected.",
        )
    proposal.status = "rejected"
    db.commit()
    db.refresh(proposal)
    return proposal


def create_income_source(db: Session, user_id: UUID, payload: IncomeSourceCreate) -> IncomeSource:
    source = IncomeSource(user_id=user_id, **payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def list_income_sources(db: Session, user_id: UUID) -> list[IncomeSource]:
    return list(
        db.scalars(
            select(IncomeSource).where(IncomeSource.user_id == user_id).order_by(IncomeSource.created_at.desc())
        )
    )


def create_obligation(db: Session, user_id: UUID, payload: ObligationCreate) -> FinancialObligation:
    obligation = FinancialObligation(user_id=user_id, **payload.model_dump())
    db.add(obligation)
    db.commit()
    db.refresh(obligation)
    return obligation


def list_obligations(db: Session, user_id: UUID) -> list[FinancialObligation]:
    return list(
        db.scalars(
            select(FinancialObligation)
            .where(FinancialObligation.user_id == user_id)
            .order_by(FinancialObligation.created_at.desc())
        )
    )


def create_goal(db: Session, user_id: UUID, payload: GoalCreate) -> Goal:
    context = db.get(FinancialContext, user_id)
    current_amount = Decimal("0")
    has_active_goal = db.scalar(select(Goal.id).where(Goal.user_id == user_id, Goal.status == "active")) is not None
    if context is not None and not has_active_goal:
        _recalculate_current_savings(context)
        current_amount = min(
            context.current_savings,
            payload.target_amount,
        )
    goal = Goal(user_id=user_id, current_amount=current_amount, **payload.model_dump())
    db.add(goal)
    db.flush()
    now = datetime.now(timezone.utc)
    milestones = []
    for amount, title in _default_milestones(goal.target_amount):
        milestones.append(
            GoalMilestone(
                goal_id=goal.id,
                amount=amount,
                title=title,
                is_completed=current_amount >= amount,
                completed_at=now if current_amount >= amount else None,
            )
        )
    db.add_all(milestones)
    if current_amount >= goal.target_amount:
        goal.status = "completed"
    db.commit()
    db.refresh(goal)
    return goal


def list_goals(db: Session, user_id: UUID) -> list[Goal]:
    goals = list(db.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())))
    context = db.get(FinancialContext, user_id)
    if context is not None and _sync_unallocated_goal_progress(db, user_id, context):
        db.commit()
        for goal in goals:
            db.refresh(goal)
    return goals


def get_goal_details(db: Session, user_id: UUID, goal_id: UUID) -> Goal:
    goal = db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id))
    if goal is None:
        raise _not_found("Goal not found.")
    return goal


def distribute_savings(
    db: Session,
    user_id: UUID,
    payload: SavingsDistributionCreate,
) -> list[Transaction]:
    allocation_by_goal: dict[UUID, Decimal] = {}
    for allocation in payload.allocations:
        allocation_by_goal[allocation.goal_id] = allocation_by_goal.get(allocation.goal_id, Decimal("0")) + allocation.amount

    total_allocated = sum(allocation_by_goal.values(), Decimal("0"))
    if total_allocated != payload.amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The allocation total must equal the savings amount.",
        )

    goals = {
        goal.id: goal
        for goal in db.scalars(
            select(Goal).where(Goal.user_id == user_id, Goal.id.in_(allocation_by_goal.keys()))
        )
    }
    if len(goals) != len(allocation_by_goal):
        raise _not_found("One or more goals were not found for this user.")

    for goal_id, amount in allocation_by_goal.items():
        if amount <= 0:
            continue
        goal = goals[goal_id]
        if goal.status != "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active goals can receive contributions.")
        remaining = max(goal.target_amount - goal.current_amount, Decimal("0"))
        if amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Contribution to {goal.name} exceeds its remaining amount of {remaining}.",
            )

    transactions: list[Transaction] = []
    for goal_id, amount in allocation_by_goal.items():
        if amount <= 0:
            continue
        goal = goals[goal_id]
        proposal = create_transaction_proposal(
            db,
            user_id,
            TransactionProposalCreate(
                transaction_type="saving",
                amount=amount,
                currency=goal.currency,
                category="goal_saving",
                description=f"Saved for {goal.name}",
                date=local_today(),
                source="web",
                confidence=Decimal("1"),
                raw_statement=f"Saved {amount} for {goal.name}",
                goal_id=goal_id,
            ),
        )
        transactions.append(confirm_transaction_proposal(db, user_id, proposal.id))
    return transactions


def list_transactions(db: Session, user_id: UUID) -> list[Transaction]:
    return list(
        db.scalars(
            select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.transaction_date.desc())
        )
    )


def get_financial_context(db: Session, user_id: UUID) -> FinancialContext:
    context = ensure_financial_context(db, user_id)
    _recalculate_current_savings(context)
    _sync_unallocated_goal_progress(db, user_id, context)
    db.commit()
    db.refresh(context)
    return context
