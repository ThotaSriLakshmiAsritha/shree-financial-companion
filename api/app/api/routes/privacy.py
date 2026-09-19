from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    AuthenticatedUser,
    get_current_profile,
    get_current_user,
)
from app.auth.models import Profile
from app.db.session import get_db
from app.privacy.schemas import AccountDeletionRequest, AuditEventResponse
from app.privacy.service import delete_owned_account, list_owned_audit_events

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.get("/audit-events", response_model=list[AuditEventResponse])
def read_audit_events(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> list[AuditEventResponse]:
    return list_owned_audit_events(db, profile.id)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: AccountDeletionRequest,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
    auth_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> Response:
    delete_owned_account(db, profile, auth_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
