from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_profile
from app.auth.models import Profile
from app.conversation.orchestrator import ConversationOrchestrator
from app.conversation.schemas import (
    ConversationMessageRequest,
    ConversationMessageResponse,
)
from app.db.session import get_db

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/message", response_model=ConversationMessageResponse)
def handle_message(
    payload: ConversationMessageRequest,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> ConversationMessageResponse:
    try:
        return ConversationOrchestrator().handle(db, profile, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
