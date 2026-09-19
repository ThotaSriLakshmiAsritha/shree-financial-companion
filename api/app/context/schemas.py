from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.education.state_machine import ApplicationState, KnowledgeState


class EducationalContextUpsert(BaseModel):
    concept: str = Field(min_length=1, max_length=100)
    knowledge_state: KnowledgeState = KnowledgeState.NOT_INTRODUCED
    application_state: ApplicationState | None = ApplicationState.NOT_OBSERVED
    reasoning: str | None = Field(default=None, max_length=1000)
    misconceptions: str | None = Field(default=None, max_length=1000)
    reinforcement_needed: bool = False
    confidence: Decimal = Field(default=0, ge=0, le=1)


class EducationalContextResponse(EducationalContextUpsert):
    id: UUID
    user_id: UUID
    last_discussed: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    memory_type: str = Field(default="conversation", min_length=1, max_length=40)
    source: str = Field(default="conversation", min_length=1, max_length=30)
    importance: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)


class MemoryResponse(MemoryCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    last_retrieved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    channel: str = Field(pattern="^(web|voice|feature_phone)$")
    language: str = Field(pattern="^(en|te|hi)$")


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    channel: str
    language: str
    started_at: datetime
    ended_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationMessageCreate(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    message: str = Field(min_length=1, max_length=8000)
    language: str = Field(pattern="^(en|te|hi)$")
    intent: str | None = Field(default=None, max_length=60)
    metadata: dict[str, object] | None = None


class ConversationMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    message: str
    language: str
    intent: str | None
    metadata: dict[str, object] | None = Field(
        default=None,
        validation_alias="message_metadata",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ActiveGoalContext(BaseModel):
    name: str
    target_amount: Decimal
    current_amount: Decimal
    currency: str
    target_date: str | None


class FinancialContextSlice(BaseModel):
    income_pattern: str | None
    current_savings: Decimal
    active_goal: ActiveGoalContext | None


class EducationalContextSlice(BaseModel):
    concept: str
    knowledge_state: str
    application_state: str | None
    reinforcement_needed: bool
    reasoning: str | None


class MemoryContextSlice(BaseModel):
    content: str
    memory_type: str
    importance: Decimal


class ConversationContextSlice(BaseModel):
    role: str
    message: str
    language: str
    intent: str | None
    created_at: datetime


class UserContextSlice(BaseModel):
    display_name: str | None
    language: str


class ContextPackage(BaseModel):
    user: UserContextSlice
    financial: FinancialContextSlice
    educational: list[EducationalContextSlice]
    relevant_memory: list[MemoryContextSlice]
    recent_conversation: list[ConversationContextSlice]

    def to_prompt_text(self) -> str:
        lines = [
            "USER",
            f"Language: {self.user.language}",
            f"Name: {self.user.display_name or 'not provided'}",
            "",
            "FINANCIAL",
            f"- income pattern: {self.financial.income_pattern or 'unknown'}",
            f"- current savings: {self.financial.current_savings}",
        ]
        if self.financial.active_goal:
            goal = self.financial.active_goal
            lines.extend(
                [
                    f"- active goal: {goal.name}",
                    f"- goal progress: {goal.current_amount} / {goal.target_amount} {goal.currency}",
                ]
            )
        else:
            lines.append("- active goal: none")

        lines.append("")
        lines.append("EDUCATIONAL")
        if self.educational:
            for item in self.educational:
                reinforcement = "needs reinforcement" if item.reinforcement_needed else "no reinforcement flag"
                application = item.application_state or "NOT_OBSERVED"
                lines.append(f"- {item.concept}: {item.knowledge_state}; application: {application}; {reinforcement}")
        else:
            lines.append("- no educational context recorded")

        lines.append("")
        lines.append("RELEVANT MEMORY")
        if self.relevant_memory:
            for item in self.relevant_memory:
                lines.append(f"- {item.content}")
        else:
            lines.append("- no relevant memory retrieved")

        lines.append("")
        lines.append("RECENT CONVERSATION")
        if self.recent_conversation:
            for item in self.recent_conversation:
                lines.append(f"- {item.role} ({item.language}): {item.message}")
        else:
            lines.append("- no recent conversation")
        return "\n".join(lines)


class ContextResponse(BaseModel):
    context: ContextPackage
    prompt: str
