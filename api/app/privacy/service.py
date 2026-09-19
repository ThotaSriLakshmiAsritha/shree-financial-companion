import json
import logging
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.dependencies import AuthenticatedUser
from app.auth.models import Profile, UserIdentity, UserPreference
from app.context.models import (
    Conversation,
    ConversationMessage,
    EducationalContext,
    Memory,
)
from app.core.config import get_settings
from app.financial.models import (
    FinancialContext,
    FinancialObligation,
    Goal,
    IncomeSource,
    Transaction,
    TransactionProposal,
)
from app.privacy.models import AuditEvent
from app.voice.models import VoiceCallSession

logger = logging.getLogger(__name__)


def record_audit_event(
    db: Session,
    user_id: UUID | None,
    event_type: str,
    *,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    channel: str | None = None,
    details: str | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        channel=channel,
        details=details,
        event_metadata=metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_owned_audit_events(db: Session, user_id: UUID, limit: int = 100) -> list[AuditEvent]:
    bounded_limit = min(max(limit, 1), 100)
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.user_id == user_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(bounded_limit)
        )
    )


def _delete_supabase_auth_user(subject: str) -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account deletion is temporarily unavailable because secure auth deletion is not configured.",
        )
    try:
        response = httpx.delete(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{subject}",
            headers={
                "apikey": settings.supabase_service_role_key,
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
            },
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Supabase account deletion failed to connect: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account deletion service is unavailable. No application data was deleted.",
        ) from exc
    if response.status_code not in {200, 204}:
        logger.warning("Supabase account deletion failed with status %s", response.status_code)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account deletion could not be completed. No application data was deleted.",
        )


def delete_owned_account(db: Session, profile: Profile, auth_user: AuthenticatedUser) -> None:
    """Delete auth and all owned application data as one deliberate user action."""

    # Delete the auth identity first. If this fails, the application data remains intact.
    _delete_supabase_auth_user(auth_user.subject)

    # Keep only a non-owned deletion audit marker; all other user-linked audit data is removed.
    db.execute(delete(AuditEvent).where(AuditEvent.user_id == profile.id))
    deletion_event = AuditEvent(
        user_id=None,
        event_type="account.deleted",
        resource_type="profile",
        resource_id=profile.id,
        details="The user requested deletion of their account and application data.",
        event_metadata={"auth_subject_deleted": True},
    )
    db.add(deletion_event)

    # Explicit deletes keep local SQLite behavior equivalent to PostgreSQL CASCADE behavior.
    conversation_ids = select(Conversation.id).where(Conversation.user_id == profile.id)
    db.execute(delete(VoiceCallSession).where(VoiceCallSession.user_id == profile.id))
    db.execute(delete(ConversationMessage).where(ConversationMessage.conversation_id.in_(conversation_ids)))
    db.execute(delete(Conversation).where(Conversation.user_id == profile.id))
    db.execute(delete(EducationalContext).where(EducationalContext.user_id == profile.id))
    db.execute(delete(Memory).where(Memory.user_id == profile.id))
    db.execute(delete(Transaction).where(Transaction.user_id == profile.id))
    db.execute(delete(TransactionProposal).where(TransactionProposal.user_id == profile.id))
    db.execute(delete(FinancialObligation).where(FinancialObligation.user_id == profile.id))
    db.execute(delete(IncomeSource).where(IncomeSource.user_id == profile.id))
    db.execute(delete(Goal).where(Goal.user_id == profile.id))
    db.execute(delete(FinancialContext).where(FinancialContext.user_id == profile.id))
    db.execute(delete(UserPreference).where(UserPreference.user_id == profile.id))
    db.execute(delete(UserIdentity).where(UserIdentity.user_id == profile.id))
    db.execute(delete(Profile).where(Profile.id == profile.id))
    db.commit()


def audit_metadata_json(metadata: dict[str, object] | None) -> str | None:
    return json.dumps(metadata, default=str, ensure_ascii=False) if metadata else None
