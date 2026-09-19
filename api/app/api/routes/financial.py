from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_profile
from app.auth.models import Profile
from app.db.session import get_db
from app.financial.schemas import (
    FinancialContextResponse,
    GoalCreate,
    GoalDetailsResponse,
    GoalResponse,
    IncomeSourceCreate,
    IncomeSourceResponse,
    ObligationCreate,
    ObligationResponse,
    TransactionProposalCreate,
    TransactionProposalResponse,
    TransactionResponse,
    SavingsDistributionCreate,
)
from app.financial.service import (
    confirm_transaction_proposal,
    create_goal,
    create_income_source,
    create_obligation,
    create_transaction_proposal,
    distribute_savings,
    get_goal_details,
    get_financial_context,
    list_goals,
    list_income_sources,
    list_obligations,
    list_transaction_proposals,
    list_transactions,
    reject_transaction_proposal,
)
from app.privacy.service import record_audit_event

router = APIRouter(prefix="/financial", tags=["financial"])


@router.get("/context", response_model=FinancialContextResponse)
def read_context(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> FinancialContextResponse:
    return get_financial_context(db, profile.id)


@router.get("/transactions", response_model=list[TransactionResponse])
def read_transactions(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> list[TransactionResponse]:
    return list_transactions(db, profile.id)


@router.post("/proposals", response_model=TransactionProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: TransactionProposalCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> TransactionProposalResponse:
    proposal = create_transaction_proposal(db, profile.id, payload)
    record_audit_event(
        db,
        profile.id,
        "financial.proposal_created",
        resource_type="transaction_proposal",
        resource_id=proposal.id,
        metadata={"transaction_type": proposal.transaction_type},
    )
    return proposal


@router.get("/proposals", response_model=list[TransactionProposalResponse])
def read_proposals(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
    pending_only: bool = Query(default=False),
) -> list[TransactionProposalResponse]:
    return list_transaction_proposals(db, profile.id, pending_only)


@router.post("/proposals/{proposal_id}/confirm", response_model=TransactionResponse)
def confirm_proposal(
    proposal_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> TransactionResponse:
    transaction = confirm_transaction_proposal(db, profile.id, proposal_id)
    record_audit_event(
        db,
        profile.id,
        "financial.transaction_confirmed",
        resource_type="transaction",
        resource_id=transaction.id,
        metadata={"transaction_type": transaction.transaction_type},
    )
    return transaction


@router.post("/proposals/{proposal_id}/reject", response_model=TransactionProposalResponse)
def reject_proposal(
    proposal_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> TransactionProposalResponse:
    proposal = reject_transaction_proposal(db, profile.id, proposal_id)
    record_audit_event(
        db,
        profile.id,
        "financial.proposal_rejected",
        resource_type="transaction_proposal",
        resource_id=proposal.id,
    )
    return proposal


@router.post("/income-sources", response_model=IncomeSourceResponse, status_code=status.HTTP_201_CREATED)
def add_income_source(
    payload: IncomeSourceCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> IncomeSourceResponse:
    return create_income_source(db, profile.id, payload)


@router.get("/income-sources", response_model=list[IncomeSourceResponse])
def read_income_sources(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> list[IncomeSourceResponse]:
    return list_income_sources(db, profile.id)


@router.post("/obligations", response_model=ObligationResponse, status_code=status.HTTP_201_CREATED)
def add_obligation(
    payload: ObligationCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> ObligationResponse:
    return create_obligation(db, profile.id, payload)


@router.get("/obligations", response_model=list[ObligationResponse])
def read_obligations(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> list[ObligationResponse]:
    return list_obligations(db, profile.id)


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def add_goal(
    payload: GoalCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> GoalResponse:
    return create_goal(db, profile.id, payload)


@router.get("/goals", response_model=list[GoalResponse])
def read_goals(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> list[GoalResponse]:
    return list_goals(db, profile.id)


@router.get("/goals/{goal_id}", response_model=GoalDetailsResponse)
def read_goal_details(
    goal_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> GoalDetailsResponse:
    return get_goal_details(db, profile.id, goal_id)


@router.post("/goals/savings/distribute", response_model=list[TransactionResponse], status_code=status.HTTP_201_CREATED)
def distribute_goal_savings(
    payload: SavingsDistributionCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> list[TransactionResponse]:
    transactions = distribute_savings(db, profile.id, payload)
    for transaction in transactions:
        record_audit_event(
            db,
            profile.id,
            "financial.goal_contribution_added",
            resource_type="transaction",
            resource_id=transaction.id,
            metadata={"goal_id": str(transaction.goal_id), "amount": str(transaction.amount)},
        )
    return transactions
