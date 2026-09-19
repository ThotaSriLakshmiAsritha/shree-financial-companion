from decimal import Decimal
from uuid import uuid4

from app.auth.models import Profile
from app.context.models import ConversationMessage
from app.conversation.orchestrator import ConversationOrchestrator
from app.conversation.schemas import (
    ConversationMessageRequest,
    GeminiResponsePayload,
    Intent,
    LanguageCode,
)
from app.db.base import Base
from app.financial.models import Transaction, TransactionProposal
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


class FakeGeminiClient:
    def __init__(self, response: str = "I can help with that.") -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def generate_response(self, **kwargs: str) -> GeminiResponsePayload:
        self.calls.append(kwargs)
        return GeminiResponsePayload(response=self.response)


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_orchestrator_extracts_proposal_without_inserting_transaction() -> None:
    db = make_session()
    profile = Profile(id=uuid4(), preferred_language="en", display_name="Lakshmi")
    db.add(profile)
    db.commit()
    gemini = FakeGeminiClient("I understood your expense. Please confirm it before recording it.")

    result = ConversationOrchestrator(gemini).handle(
        db,
        profile,
        ConversationMessageRequest(message="I spent ₹250 on school books yesterday."),
    )

    proposal = db.scalar(select(TransactionProposal).where(TransactionProposal.user_id == profile.id))
    assert result.intent is Intent.LOG_TRANSACTION
    assert result.language is LanguageCode.ENGLISH
    assert result.transaction_proposal is not None
    assert result.transaction_proposal.amount == Decimal(250)
    assert result.transaction_proposal.status == "pending"
    assert "not been recorded yet" in result.response
    assert proposal is not None
    assert db.scalar(select(Transaction).where(Transaction.user_id == profile.id)) is None
    assert db.scalar(select(ConversationMessage).where(ConversationMessage.role == "assistant")) is not None
    assert gemini.calls
    assert "250" in gemini.calls[0]["extracted_entities"]


def test_high_risk_safety_path_does_not_call_gemini() -> None:
    db = make_session()
    profile = Profile(id=uuid4(), preferred_language="te")
    db.add(profile)
    db.commit()
    gemini = FakeGeminiClient()

    result = ConversationOrchestrator(gemini).handle(
        db,
        profile,
        ConversationMessageRequest(message="They asked me to share my OTP immediately."),
    )

    assert result.intent is Intent.SCAM_REPORT
    assert result.safety.risk_level == "high"
    assert result.safety.allow_llm is False
    assert not gemini.calls
    assert "OTP" in result.response


def test_language_detection_and_message_persistence_use_same_conversation() -> None:
    db = make_session()
    profile = Profile(id=uuid4(), preferred_language="en")
    db.add(profile)
    db.commit()
    gemini = FakeGeminiClient()

    first = ConversationOrchestrator(gemini).handle(
        db,
        profile,
        ConversationMessageRequest(message="నాకు బడ్జెట్ గురించి చెప్పండి"),
    )
    second = ConversationOrchestrator(gemini).handle(
        db,
        profile,
        ConversationMessageRequest(
            conversation_id=first.conversation_id,
            message="Now explain it simply.",
        ),
    )

    assert first.language is LanguageCode.TELUGU
    assert second.conversation_id == first.conversation_id
    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == first.conversation_id)
            .order_by(ConversationMessage.created_at, ConversationMessage.id)
        )
    )
    assert [message.role for message in messages] == ["user", "assistant", "user", "assistant"]
