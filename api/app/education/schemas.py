from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.education.state_machine import (
    ApplicationState,
    KnowledgeState,
    LearningEvidenceType,
)


class EducationalEvidenceCreate(BaseModel):
    concept: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1, max_length=2000)
    evidence_type: LearningEvidenceType | None = None
    confidence: Decimal = Field(default=Decimal("0.8"), ge=0, le=1)
    reasoning: str | None = Field(default=None, max_length=1000)


class EducationalEvidenceResponse(BaseModel):
    context_id: UUID
    concept: str
    evidence_type: LearningEvidenceType
    previous_knowledge_state: KnowledgeState
    knowledge_state: KnowledgeState
    application_state: ApplicationState
    confidence: Decimal
    reinforcement_needed: bool
    reasoning: str | None
