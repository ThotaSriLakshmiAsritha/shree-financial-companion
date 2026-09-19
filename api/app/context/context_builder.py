from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.models import Profile
from app.context.conversation_context_service import list_recent_conversation
from app.context.educational_context_service import list_educational_context
from app.context.financial_context_service import build_financial_context
from app.context.memory_service import retrieve_relevant_memories
from app.context.schemas import ContextPackage


def build_context_package(
    db: Session,
    user_id: UUID,
    query: str | None = None,
) -> ContextPackage:
    """Build the only context shape that should be supplied to a future LLM call."""
    profile = db.get(Profile, user_id)
    if profile is None:
        raise LookupError("Profile not found.")

    return ContextPackage(
        user={
            "display_name": profile.display_name,
            "language": profile.preferred_language,
        },
        financial=build_financial_context(db, user_id),
        educational=list_educational_context(db, user_id, limit=6),
        relevant_memory=retrieve_relevant_memories(db, user_id, query=query, limit=3),
        recent_conversation=list_recent_conversation(db, user_id, limit=6),
    )
