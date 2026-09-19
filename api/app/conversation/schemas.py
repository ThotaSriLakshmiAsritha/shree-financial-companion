from datetime import date as Date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class Intent(StrEnum):
    LOG_TRANSACTION = "log_transaction"
    CHECK_BALANCE = "check_balance"
    CREATE_GOAL = "create_goal"
    FINANCIAL_QUESTION = "financial_question"
    LEARN_CONCEPT = "learn_concept"
    SCAM_REPORT = "scam_report"
    GENERAL_CONVERSATION = "general_conversation"
    UNKNOWN = "unknown"


class LanguageCode(StrEnum):
    ENGLISH = "en"
    HINDI = "hi"
    TELUGU = "te"


class ConversationMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None
    channel: str = Field(default="web", pattern="^(web|voice|feature_phone)$")
    language: LanguageCode | None = None


class LanguageDetectionResult(BaseModel):
    language: LanguageCode
    confidence: Decimal = Field(ge=0, le=1)
    method: str


class IntentDetectionResult(BaseModel):
    intent: Intent
    confidence: Decimal = Field(ge=0, le=1)
    matched_terms: list[str] = Field(default_factory=list)


class ExtractedTransaction(BaseModel):
    transaction_type: str = Field(pattern="^(income|expense|saving)$")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    date: Date
    source: str = Field(min_length=2, max_length=30)
    confidence: Decimal = Field(ge=0, le=1)
    raw_statement: str = Field(min_length=1, max_length=2000)
    goal_id: UUID | None = None


class SafetyAssessment(BaseModel):
    risk_level: str = Field(pattern="^(low|medium|high)$")
    flags: list[str] = Field(default_factory=list)
    allowed: bool = True
    allow_llm: bool = True
    guidance: str | None = None
    disclosure_required: bool = False


class GeminiResponsePayload(BaseModel):
    response: str = Field(min_length=1, max_length=4000)
    suggested_next_step: str | None = Field(default=None, max_length=500)
    asks_confirmation: bool = False

    model_config = {"extra": "forbid"}


class TransactionProposalSummary(BaseModel):
    id: UUID
    transaction_type: str
    amount: Decimal
    currency: str
    category: str | None
    description: str | None
    date: Date
    status: str
    requires_confirmation: bool = True


class ConversationMessageResponse(BaseModel):
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    language: LanguageCode
    intent: Intent
    response: str
    suggested_next_step: str | None
    safety: SafetyAssessment
    transaction_proposal: TransactionProposalSummary | None = None
