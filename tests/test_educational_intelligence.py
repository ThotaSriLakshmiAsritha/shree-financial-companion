from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from app.auth.models import Profile
from app.context.models import EducationalContext
from app.db.base import Base
from app.education.intelligence_service import (
    detect_learning_evidence,
    record_learning_evidence,
)
from app.education.schemas import EducationalEvidenceCreate
from app.education.state_machine import (
    ApplicationState,
    KnowledgeState,
    LearningEvidenceType,
    can_transition,
)
from pydantic import ValidationError
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


def test_application_evidence_promotes_budgeting_and_records_application() -> None:
    db = make_session()
    user_id = uuid4()
    db.add(Profile(id=user_id, preferred_language="en"))
    db.add(
        EducationalContext(
            user_id=user_id,
            concept="budgeting",
            knowledge_state=KnowledgeState.BASIC_UNDERSTANDING.value,
            application_state=ApplicationState.ATTEMPTED.value,
            confidence=Decimal("0.5"),
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    result = record_learning_evidence(
        db,
        user_id,
        EducationalEvidenceCreate(
            concept="budgeting",
            statement="I kept money aside for school expenses before buying something unnecessary.",
            confidence=Decimal("0.9"),
        ),
    )

    assert result.evidence_type is LearningEvidenceType.APPLIED
    assert result.previous_knowledge_state is KnowledgeState.BASIC_UNDERSTANDING
    assert result.knowledge_state is KnowledgeState.STRONG_UNDERSTANDING
    assert result.application_state is ApplicationState.SUCCESSFULLY_APPLIED
    assert result.confidence == Decimal("0.9")
    assert result.reinforcement_needed is False
    assert "school expenses" in (result.reasoning or "")


def test_clarification_and_misunderstanding_are_corrective_states() -> None:
    assert detect_learning_evidence("I don't understand loan interest yet.") is LearningEvidenceType.NEEDS_CLARIFICATION
    assert detect_learning_evidence("I misunderstood the interest calculation.") is LearningEvidenceType.MISUNDERSTOOD
    assert can_transition(KnowledgeState.STRONG_UNDERSTANDING, KnowledgeState.NEEDS_CLARIFICATION)
    assert not can_transition(KnowledgeState.SUCCESSFULLY_APPLIED, KnowledgeState.INTRODUCED)


def test_unrecognized_evidence_does_not_mutate_state() -> None:
    db = make_session()
    user_id = uuid4()
    db.add(Profile(id=user_id, preferred_language="en"))
    db.commit()

    with pytest.raises(ValueError, match="No educational evidence"):
        record_learning_evidence(
            db,
            user_id,
            EducationalEvidenceCreate(concept="budgeting", statement="The weather is pleasant."),
        )

    assert db.query(EducationalContext).count() == 0


def test_evidence_schema_rejects_unknown_state() -> None:
    with pytest.raises(ValidationError):
        EducationalEvidenceCreate(
            concept="budgeting",
            statement="I understand budgeting.",
            evidence_type="unsupported",
        )
