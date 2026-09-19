import datetime as dt
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class VoiceTurnRequest(BaseModel):
    call_id: str
    caller_number: str | None = None
    audio_base64: str
    audio_mime_type: str = "audio/wav"
    idempotency_key: str | None = None


class VoiceTurnResponse(BaseModel):
    user_id: UUID
    conversation_id: UUID
    language: Any
    response_audio_base64: str
    response_audio_mime_type: str = "audio/wav"
    transcript: str | None = None
    proposal_id: UUID | None = None


class VoiceWebhookAck(BaseModel):
    accepted: bool = True
    call_id: str | None = None
    detail: str | None = None


class BrowserVoiceTurnRequest(BaseModel):
    call_id: str = "browser-turn"
    audio_base64: str
    audio_mime_type: str = "audio/webm"
    idempotency_key: str | None = None


class BrowserVoiceTranscriptResponse(BaseModel):
    transcript: str
    language: str
    request_id: str | None = None


class SarvamAgentContextRequest(BaseModel):
    user_phone_number: str
    query: str | None = None


class SarvamAgentTransactionRequest(BaseModel):
    user_phone_number: str
    action: Literal["propose", "confirm", "reject"]
    transaction_type: Literal["income", "expense"] | None = None
    amount: float | Decimal | None = None
    currency: str = "INR"
    category: str | None = None
    description: str | None = None
    date: dt.date | None = None
    confidence: float = 1.0
    raw_statement: str | None = None
    proposal_id: UUID | None = None
    interaction_id: str | None = None


class SarvamAgentActionResponse(BaseModel):
    status: str
    proposal_id: UUID | None = None
    transaction_id: UUID | None = None
    message: str | None = None


class SarvamAgentStoryRequest(BaseModel):
    user_phone_number: str
    slug: str | None = None
    language: str | None = None


class SarvamAgentStoryResponse(BaseModel):
    story_slug: str
    story_key: str
    language_code: str
    scene_index: int = 0
    total_scenes: int = 1
    text: str
    pause_after_ms: int = 0


class SarvamTurnRecord(BaseModel):
    role: str
    indic_text: str | None = None
    en_text: str | None = None


class SarvamDeploymentWebhook(BaseModel):
    app_id: str | None = None
    interaction_id: str
    user_phone_number: str
    interaction_transcript: list[SarvamTurnRecord] | None = None


class SarvamWebhookAck(BaseModel):
    accepted: bool = True
    interaction_id: str
    user_id: UUID | None = None
    duplicate: bool = False
    detail: str | None = None
