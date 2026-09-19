from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_profile
from app.auth.models import Profile
from app.context.context_builder import build_context_package
from app.context.conversation_context_service import append_message, create_conversation
from app.context.educational_context_service import (
    serialize_educational_context,
    upsert_educational_context,
)
from app.context.memory_service import create_memory
from app.context.schemas import (
    ContextResponse,
    ConversationCreate,
    ConversationMessageCreate,
    ConversationMessageResponse,
    ConversationResponse,
    EducationalContextResponse,
    EducationalContextUpsert,
    MemoryCreate,
    MemoryResponse,
)
from app.db.session import get_db
from app.education.intelligence_service import record_learning_evidence
from app.education.schemas import EducationalEvidenceCreate, EducationalEvidenceResponse

router = APIRouter(prefix="/context", tags=["context"])


@router.get("", response_model=ContextResponse)
def read_context_package(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
    query: str | None = Query(default=None, max_length=500),
) -> ContextResponse:
    package = build_context_package(db, profile.id, query=query)
    return ContextResponse(context=package, prompt=package.to_prompt_text())


@router.post(
    "/educational",
    response_model=EducationalContextResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_educational_context(
    payload: EducationalContextUpsert,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> EducationalContextResponse:
    try:
        return serialize_educational_context(upsert_educational_context(db, profile.id, payload))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post(
    "/educational/evidence",
    response_model=EducationalEvidenceResponse,
)
def record_educational_evidence(
    payload: EducationalEvidenceCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> EducationalEvidenceResponse:
    try:
        return record_learning_evidence(db, profile.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def record_memory(
    payload: MemoryCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> MemoryResponse:
    return create_memory(db, profile.id, payload)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def start_conversation(
    payload: ConversationCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> ConversationResponse:
    return create_conversation(db, profile.id, payload)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_conversation_message(
    conversation_id: UUID,
    payload: ConversationMessageCreate,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> ConversationMessageResponse:
    try:
        return append_message(db, profile.id, conversation_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
