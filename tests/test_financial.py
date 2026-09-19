from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from app.auth.models import Profile
from app.db.base import Base
from app.financial.models import FinancialContext, Goal, GoalContribution, GoalMilestone, Transaction
from app.financial.schemas import GoalAllocationCreate, GoalCreate, SavingsDistributionCreate, TransactionProposalCreate
from app.financial.service import (
    confirm_transaction_proposal,
    create_goal,
    create_transaction_proposal,
    distribute_savings,
    get_goal_details,
)
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def test_financial_write_requires_proposal_confirmation() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    user_id = uuid4()

    with Session(engine) as db:
        db.add(Profile(id=user_id, display_name="Lakshmi"))
        db.commit()

        goal = create_goal(
            db,
            user_id,
            GoalCreate(name="Sewing machine", target_amount=Decimal(15000)),
        )
        proposal = create_transaction_proposal(
            db,
            user_id,
            TransactionProposalCreate(
                transaction_type="saving",
                amount=Decimal(500),
                category="goal_saving",
                description="Saved for the sewing machine",
                date=date(2026, 9, 18),
                source="voice",
                confidence=Decimal("0.97"),
                raw_statement="ఈరోజు ₹500 దాచాను",
                goal_id=goal.id,
            ),
        )

        assert db.scalar(select(Transaction).where(Transaction.user_id == user_id)) is None
        assert proposal.status == "pending"

        transaction = confirm_transaction_proposal(db, user_id, proposal.id)

        assert transaction.confirmation_status == "confirmed"
        assert transaction.proposal_id == proposal.id
        assert db.scalar(select(Transaction).where(Transaction.user_id == user_id)) is not None

        context = db.get(FinancialContext, user_id)
        refreshed_goal = db.get(Goal, goal.id)
        assert context is not None
        assert context.total_savings == Decimal("500.00")
        assert context.current_savings == Decimal("500.00")
        assert refreshed_goal is not None
        assert refreshed_goal.current_amount == Decimal("500.00")

        with pytest.raises(HTTPException) as duplicate_confirmation:
            confirm_transaction_proposal(db, user_id, proposal.id)
        assert duplicate_confirmation.value.status_code == 409


def test_multiple_goals_have_independent_milestones_and_contributions() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    user_id = uuid4()

    with Session(engine) as db:
        db.add(Profile(id=user_id, display_name="Lakshmi"))
        db.commit()
        first = create_goal(db, user_id, GoalCreate(name="Sewing machine", target_amount=Decimal("1000")))
        second = create_goal(db, user_id, GoalCreate(name="School fees", target_amount=Decimal("2000")))

        transactions = distribute_savings(
            db,
            user_id,
            SavingsDistributionCreate(
                amount=Decimal("300"),
                allocations=[
                    GoalAllocationCreate(goal_id=first.id, amount=Decimal("200")),
                    GoalAllocationCreate(goal_id=second.id, amount=Decimal("100")),
                ],
            ),
        )

        refreshed_first = db.get(Goal, first.id)
        refreshed_second = db.get(Goal, second.id)
        assert len(transactions) == 2
        assert refreshed_first is not None and refreshed_first.current_amount == Decimal("200.00")
        assert refreshed_second is not None and refreshed_second.current_amount == Decimal("100.00")
        assert db.query(GoalMilestone).filter_by(goal_id=first.id).count() == 4
        assert db.query(GoalMilestone).filter_by(goal_id=second.id).count() == 4
        assert db.query(GoalContribution).filter_by(goal_id=first.id).count() == 1
        assert db.query(GoalContribution).filter_by(goal_id=second.id).count() == 1
        details = get_goal_details(db, user_id, first.id)
        assert len(details.milestones) == 4
        assert len(details.contributions) == 1
