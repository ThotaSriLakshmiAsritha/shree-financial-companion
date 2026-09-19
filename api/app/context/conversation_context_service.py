from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context.models import Conversation, ConversationMessage
from app.context.schemas import (
    ConversationContextSlice,
    ConversationCreate,
    ConversationMessageCreate,
)


def create_conversation(db: Session, user_id: UUID, payload: ConversationCreate) -> Conversation:
    conversation = Conversation(user_id=user_id, **payload.model_dump())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def append_message(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
    payload: ConversationMessageCreate,
) -> ConversationMessage:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    if conversation is None:
        raise LookupError("Conversation not found for this user.")

    message = ConversationMessage(
        conversation_id=conversation.id,
        role=payload.role,
        message=payload.message,
        language=payload.language,
        intent=payload.intent,
        message_metadata=payload.metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_owned_conversation(db: Session, user_id: UUID, conversation_id: UUID) -> Conversation | None:
    return db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )


def list_recent_conversation(
    db: Session,
    user_id: UUID,
    limit: int = 6,
) -> list[ConversationContextSlice]:
    conversation = db.scalar(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    if conversation is None:
        return []

    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation.id)
            .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .limit(limit)
        )
    )
    return [
        ConversationContextSlice(
            role=message.role,
            message=message.message,
            language=message.language,
            intent=message.intent,
            created_at=message.created_at,
        )
        for message in reversed(messages)
    ]
