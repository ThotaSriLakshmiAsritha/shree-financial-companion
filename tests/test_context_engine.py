from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.auth.models import Profile
from app.context.context_builder import build_context_package
from app.context.models import (
    Conversation,
    ConversationMessage,
    EducationalContext,
    Memory,
)
from app.db.base import Base
from app.financial.models import FinancialContext, Goal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_context_builder_returns_compact_relevant_package() -> None:
    db = make_session()
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    db.add(
        Profile(
            id=user_id,
            display_name="Lakshmi",
            preferred_language="te",
            onboarding_completed=True,
        )
    )
    db.add(
        FinancialContext(
            user_id=user_id,
            income_pattern="irregular",
            current_savings=Decimal(4500),
            currency="INR",
        )
    )
    db.add(
        Goal(
            user_id=user_id,
            name="Sewing machine",
            target_amount=Decimal(15000),
            current_amount=Decimal(4500),
            currency="INR",
            target_date=date(2027, 6, 1),
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db.add_all(
        [
            EducationalContext(
                user_id=user_id,
                concept="budgeting",
                knowledge_state="STRONG_UNDERSTANDING",
                application_state="SUCCESSFULLY_APPLIED",
                reinforcement_needed=False,
                confidence=Decimal("0.9"),
                updated_at=now,
            ),
            EducationalContext(
                user_id=user_id,
                concept="loan interest",
                knowledge_state="BASIC_UNDERSTANDING",
                application_state="ATTEMPTED",
                reinforcement_needed=True,
                confidence=Decimal("0.4"),
                updated_at=now + timedelta(seconds=1),
            ),
        ]
    )
    db.add_all(
        [
            Memory(
                user_id=user_id,
                content="School fees expected around June",
                memory_type="reminder",
                source="conversation",
                importance=Decimal("0.9"),
                created_at=now,
            ),
            Memory(
                user_id=user_id,
                content="Unrelated low-priority note",
                memory_type="note",
                source="conversation",
                importance=Decimal("0.1"),
                created_at=now,
            ),
        ]
    )
    conversation = Conversation(
        user_id=user_id,
        channel="web",
        language="te",
        started_at=now,
    )
    db.add(conversation)
    db.flush()
    db.add_all(
        [
            ConversationMessage(
                conversation_id=conversation.id,
                role="user",
                message="I want to plan for the school fees.",
                language="te",
                created_at=now,
            ),
            ConversationMessage(
                conversation_id=conversation.id,
                role="assistant",
                message="Let us look at your goal.",
                language="te",
                created_at=now + timedelta(seconds=1),
            ),
        ]
    )
    db.commit()

    package = build_context_package(db, user_id, query="school fees June")

    assert package.user.language == "te"
    assert package.financial.current_savings == Decimal("4500.00")
    assert package.financial.active_goal is not None
    assert package.financial.active_goal.name == "Sewing machine"
    assert [item.concept for item in package.educational] == ["loan interest", "budgeting"]
    assert package.relevant_memory[0].content == "School fees expected around June"
    assert [item.role for item in package.recent_conversation] == ["user", "assistant"]

    prompt = package.to_prompt_text()
    assert "Language: te" in prompt
    assert "current savings: 4500.00" in prompt
    assert "application: SUCCESSFULLY_APPLIED" in prompt
    assert "School fees expected around June" in prompt
    assert "Unrelated low-priority note" not in prompt
    assert "entire database" not in prompt


def test_context_package_is_bounded() -> None:
    db = make_session()
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    db.add(Profile(id=user_id, preferred_language="en"))
    db.add_all(
        [
            Memory(
                user_id=user_id,
                content=f"Memory {index}",
                importance=Decimal("0.5"),
                created_at=now + timedelta(seconds=index),
            )
            for index in range(10)
        ]
    )
    conversation = Conversation(user_id=user_id, channel="web", language="en", started_at=now)
    db.add(conversation)
    db.flush()
    db.add_all(
        [
            ConversationMessage(
                conversation_id=conversation.id,
                role="user",
                message=f"Message {index}",
                language="en",
                created_at=now + timedelta(seconds=index),
            )
            for index in range(10)
        ]
    )
    db.commit()

    package = build_context_package(db, user_id)

    assert len(package.relevant_memory) == 3
    assert len(package.recent_conversation) == 6
    assert package.recent_conversation[0].message == "Message 4"
    assert package.recent_conversation[-1].message == "Message 9"
