import re
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context.models import EducationalContext
from app.education.schemas import EducationalEvidenceCreate, EducationalEvidenceResponse
from app.education.state_machine import (
    ApplicationState,
    KnowledgeState,
    LearningEvidenceType,
    target_state_for_evidence,
)

_CLARIFICATION_MARKERS = (
    "don't understand",
    "do not understand",
    "confused",
    "not clear",
    "explain",
    "doubt",
    "అర్థం కాలేదు",
    "సందేహం",
    "समझ नहीं",
    "स्पष्ट नहीं",
)
_MISUNDERSTANDING_MARKERS = (
    "misunderstood",
    "i was wrong",
    "my mistake",
    "mistaken",
    "गलत",
    "తప్పు",
)
_APPLICATION_PATTERNS = (
    r"\bkept?\b.*\baside\b",
    r"\bset\b.*\baside\b",
    r"\b(saved|save|reserved|allocated|budgeted|planned)\b",
    r"\b(followed|used|applied|stuck to)\b.*\b(budget|plan|rule|lesson)\b",
    r"\b(before|instead of|rather than)\b.*\b(buy|buying|spend|spending|purchase)\b",
    r"దాచాను|పొదుపు|బడ్జెట్|బచత్",
    r"बचाया|अलग रख|बजट बनाया|खर्च करने के बजाय",
)
_UNDERSTANDING_MARKERS = (
    "i understand",
    "now i know",
    "makes sense",
    "got it",
    "అర్థమైంది",
    "అవగాహన",
    "समझ गया",
    "समझ आया",
)


def detect_learning_evidence(statement: str) -> LearningEvidenceType | None:
    """Infer a conservative learning signal from a user statement.

    This is intentionally a small deterministic seam. A future classifier can
    replace it without changing the state transition or persistence rules.
    """
    normalized = statement.casefold()
    if any(marker in normalized for marker in _MISUNDERSTANDING_MARKERS):
        return LearningEvidenceType.MISUNDERSTOOD
    if any(marker in normalized for marker in _CLARIFICATION_MARKERS):
        return LearningEvidenceType.NEEDS_CLARIFICATION
    if any(re.search(pattern, normalized) for pattern in _APPLICATION_PATTERNS):
        return LearningEvidenceType.APPLIED
    if any(marker in normalized for marker in _UNDERSTANDING_MARKERS):
        return LearningEvidenceType.UNDERSTOOD
    return None


def _get_or_create_context(db: Session, user_id: UUID, concept: str) -> EducationalContext:
    item = db.scalar(
        select(EducationalContext).where(
            EducationalContext.user_id == user_id,
            EducationalContext.concept == concept,
        )
    )
    if item is None:
        item = EducationalContext(
            user_id=user_id,
            concept=concept,
            knowledge_state=KnowledgeState.NOT_INTRODUCED.value,
            application_state=ApplicationState.NOT_OBSERVED.value,
        )
        db.add(item)
        db.flush()
    return item


def _append_reasoning(existing: str | None, evidence: EducationalEvidenceCreate, evidence_type: LearningEvidenceType) -> str:
    note = evidence.reasoning or f"Detected {evidence_type.value} evidence: {evidence.statement}"
    combined = f"{existing}\n{note}" if existing else note
    return combined[-4000:]


def record_learning_evidence(
    db: Session,
    user_id: UUID,
    payload: EducationalEvidenceCreate,
) -> EducationalEvidenceResponse:
    evidence_type = payload.evidence_type or detect_learning_evidence(payload.statement)
    if evidence_type is None:
        raise ValueError("No educational evidence could be detected; provide evidence_type explicitly.")

    item = _get_or_create_context(db, user_id, payload.concept)
    current_state = KnowledgeState(item.knowledge_state)
    target_state = target_state_for_evidence(current_state, evidence_type)
    previous_state = current_state
    current_confidence = Decimal(item.confidence or 0)
    if evidence_type in {
        LearningEvidenceType.NEEDS_CLARIFICATION,
        LearningEvidenceType.MISUNDERSTOOD,
    }:
        next_confidence = min(current_confidence, payload.confidence)
    else:
        next_confidence = max(current_confidence, payload.confidence)

    item.knowledge_state = target_state.value
    if evidence_type is LearningEvidenceType.APPLIED:
        item.application_state = ApplicationState.SUCCESSFULLY_APPLIED.value
    elif item.application_state is None:
        item.application_state = ApplicationState.NOT_OBSERVED.value
    item.confidence = next_confidence
    item.reinforcement_needed = target_state in {
        KnowledgeState.NEEDS_CLARIFICATION,
        KnowledgeState.MISUNDERSTOOD,
    }
    item.reasoning = _append_reasoning(item.reasoning, payload, evidence_type)
    item.last_discussed = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)

    return EducationalEvidenceResponse(
        context_id=item.id,
        concept=item.concept,
        evidence_type=evidence_type,
        previous_knowledge_state=previous_state,
        knowledge_state=target_state,
        application_state=ApplicationState(item.application_state),
        confidence=item.confidence,
        reinforcement_needed=item.reinforcement_needed,
        reasoning=item.reasoning,
    )
