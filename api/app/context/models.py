from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth import models as auth_models  # noqa: F401
from app.db.base import Base
from app.education.state_machine import ApplicationState, KnowledgeState


class EducationalContext(Base):
    __tablename__ = "educational_context"
    __table_args__ = (
        UniqueConstraint("user_id", "concept", name="uq_educational_context_user_concept"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_educational_context_confidence"),
        CheckConstraint(
            "knowledge_state IN ('NOT_INTRODUCED', 'INTRODUCED', 'BASIC_UNDERSTANDING', "
            "'STRONG_UNDERSTANDING', 'SUCCESSFULLY_APPLIED', 'NEEDS_CLARIFICATION', 'MISUNDERSTOOD')",
            name="ck_educational_context_knowledge_state",
        ),
        CheckConstraint(
            "application_state IS NULL OR application_state IN ('NOT_OBSERVED', 'ATTEMPTED', 'SUCCESSFULLY_APPLIED')",
            name="ck_educational_context_application_state",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept: Mapped[str] = mapped_column(String(100), nullable=False)
    knowledge_state: Mapped[str] = mapped_column(
        String(40), nullable=False, default=KnowledgeState.NOT_INTRODUCED.value, server_default=KnowledgeState.NOT_INTRODUCED.value
    )
    application_state: Mapped[str | None] = mapped_column(
        String(40), nullable=True, default=ApplicationState.NOT_OBSERVED.value, server_default=ApplicationState.NOT_OBSERVED.value
    )
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    misconceptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_discussed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reinforcement_needed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profile = relationship("Profile")


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint("importance >= 0 AND importance <= 1", name="ck_memories_importance"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(40), nullable=False, default="conversation", server_default="conversation")
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="conversation", server_default="conversation")
    importance: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=0.5, server_default="0.5")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile")


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('web', 'voice', 'feature_phone')",
            name="ck_conversations_channel",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_conversation_messages_role",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    intent: Mapped[str | None] = mapped_column(String(60), nullable=True)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
