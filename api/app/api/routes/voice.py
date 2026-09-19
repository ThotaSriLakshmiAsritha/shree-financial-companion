import base64
import binascii
import secrets
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_profile
from app.auth.models import Profile
from app.auth.service import normalize_phone_number
from app.context.context_builder import build_context_package
from app.context.conversation_context_service import append_message
from app.context.schemas import ConversationMessageCreate
from app.core.config import get_settings
from app.db.session import get_db
from app.financial.schemas import TransactionProposalCreate
from app.financial.service import confirm_transaction_proposal, create_transaction_proposal, reject_transaction_proposal
from app.privacy.service import record_audit_event
from app.voice.exotel_adapter import (
    ExotelClient,
    ExotelWebhookError,
    parse_exotel_event,
)
from app.voice.sarvam_client import SarvamClient, SarvamUnavailable, SpeechTranscript, internal_language_code
from app.voice.schemas import (
    BrowserVoiceTranscriptResponse,
    BrowserVoiceTurnRequest,
    SarvamAgentActionResponse,
    SarvamAgentContextRequest,
    SarvamAgentStoryRequest,
    SarvamAgentStoryResponse,
    SarvamAgentTransactionRequest,
    SarvamDeploymentWebhook,
    SarvamWebhookAck,
    VoiceTurnRequest,
    VoiceTurnResponse,
    VoiceWebhookAck,
)
from app.voice.service import handle_voice_turn
from app.voice.service import get_or_create_voice_session, get_voice_profile
from app.voice.models import VoiceCallSession
from app.stories.service import get_story, story_text

router = APIRouter(prefix="/voice/exotel", tags=["voice"])
sarvam_router = APIRouter(prefix="/voice/sarvam", tags=["voice", "sarvam-agent"])


def _verify_sarvam_agent_key(provided_key: str | None) -> None:
    settings = get_settings()
    expected_key = settings.sarvam_agent_tool_key or settings.sarvam_api_key
    if not expected_key or not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Sarvam agent credential.")


def _agent_profile(db: Session, phone_number: str, provided_key: str | None) -> Profile:
    _verify_sarvam_agent_key(provided_key)
    return get_voice_profile(db, phone_number)


@sarvam_router.post("/agent/context")
def read_sarvam_agent_context(
    payload: SarvamAgentContextRequest,
    db: Annotated[Session, Depends(get_db)],
    x_sarvam_agent_key: str | None = Header(default=None),
) -> dict[str, object]:
    """Compact, phone-scoped context tool for a deployed Sarvam Voice Agent."""
    profile = _agent_profile(db, payload.user_phone_number, x_sarvam_agent_key)
    context = build_context_package(db, profile.id, query=payload.query)
    return {
        "context": context.model_dump(mode="json"),
        "prompt": context.to_prompt_text(),
        "story_tool": {
            "method": "POST",
            "path": "/voice/sarvam/agent/story",
            "description": "Fetch one complete localized financial story in a single response so the agent can narrate it seamlessly.",
        },
    }


@sarvam_router.post("/agent/transaction", response_model=SarvamAgentActionResponse)
def sarvam_agent_transaction(
    payload: SarvamAgentTransactionRequest,
    db: Annotated[Session, Depends(get_db)],
    x_sarvam_agent_key: str | None = Header(default=None),
) -> SarvamAgentActionResponse:
    """Allow the Sarvam agent to use the same proposal/confirmation path as web and browser voice."""
    profile = _agent_profile(db, payload.user_phone_number, x_sarvam_agent_key)
    if payload.action == "propose":
        if payload.transaction_type is None or payload.amount is None or payload.description is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A transaction type, amount, and description are required.")
        proposal = create_transaction_proposal(
            db,
            profile.id,
            TransactionProposalCreate(
                transaction_type=payload.transaction_type,
                amount=Decimal(str(payload.amount)),
                currency=payload.currency,
                category=payload.category,
                description=payload.description,
                date=payload.date or date.today(),
                source="sarvam_agent",
                confidence=Decimal(str(payload.confidence)),
                raw_statement=payload.raw_statement or payload.description,
            ),
        )
        record_audit_event(
            db,
            profile.id,
            "voice.sarvam_agent_proposal_created",
            resource_type="transaction_proposal",
            resource_id=proposal.id,
            channel="feature_phone",
            metadata={"interaction_id": payload.interaction_id},
        )
        return SarvamAgentActionResponse(
            status="confirmation_required",
            proposal_id=proposal.id,
            message="Proposal created. Ask the user to confirm this transaction before calling the confirm action.",
        )

    if payload.proposal_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="proposal_id is required for this action.")
    if payload.action == "confirm":
        transaction = confirm_transaction_proposal(db, profile.id, payload.proposal_id)
        record_audit_event(
            db,
            profile.id,
            "voice.sarvam_agent_transaction_confirmed",
            resource_type="transaction",
            resource_id=transaction.id,
            channel="feature_phone",
            metadata={"interaction_id": payload.interaction_id},
        )
        return SarvamAgentActionResponse(status="confirmed", proposal_id=payload.proposal_id, transaction_id=transaction.id, message="The transaction was recorded after confirmation.")

    proposal = reject_transaction_proposal(db, profile.id, payload.proposal_id)
    record_audit_event(
        db,
        profile.id,
        "voice.sarvam_agent_proposal_rejected",
        resource_type="transaction_proposal",
        resource_id=proposal.id,
        channel="feature_phone",
        metadata={"interaction_id": payload.interaction_id},
    )
    return SarvamAgentActionResponse(status="rejected", proposal_id=proposal.id, message="The transaction proposal was rejected.")


@sarvam_router.post("/agent/story", response_model=SarvamAgentStoryResponse)
def sarvam_agent_story(
    payload: SarvamAgentStoryRequest,
    db: Annotated[Session, Depends(get_db)],
    x_sarvam_agent_key: str | None = Header(default=None),
) -> SarvamAgentStoryResponse:
    """Return one localized story scene for the deployed Sarvam voice agent.

    The agent speaks this text in the returned language; it does not get a
    separate story database or a separate financial identity.
    """
    profile = _agent_profile(db, payload.user_phone_number, x_sarvam_agent_key)
    try:
        story = get_story(db, profile, slug=payload.slug, language=payload.language)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SarvamAgentStoryResponse(
        story_slug=story.slug,
        story_key=story.story_key,
        language_code=story.language_code,
        scene_index=0,
        total_scenes=1,
        text=story_text(story),
        pause_after_ms=0,
    )


@sarvam_router.post("/webhook", response_model=SarvamWebhookAck)
async def receive_sarvam_deployment_webhook(
    payload: SarvamDeploymentWebhook,
    db: Annotated[Session, Depends(get_db)],
    x_sarvam_agent_key: str | None = Header(default=None),
) -> SarvamWebhookAck:
    """Persist a completed Sarvam call transcript without creating a second voice AI."""
    _verify_sarvam_agent_key(x_sarvam_agent_key)
    settings = get_settings()
    if settings.sarvam_agent_id and payload.app_id != settings.sarvam_agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown Sarvam agent.")
    profile = get_voice_profile(db, payload.user_phone_number)
    existing = db.scalar(
        select(VoiceCallSession).where(
            VoiceCallSession.provider == "sarvam",
            VoiceCallSession.external_call_id == payload.interaction_id,
        )
    )
    if existing is not None and existing.status == "completed":
        return SarvamWebhookAck(accepted=True, interaction_id=payload.interaction_id, user_id=profile.id, duplicate=True, detail="Webhook replay acknowledged.")

    session = get_or_create_voice_session(
        db,
        profile.id,
        normalize_phone_number(payload.user_phone_number) or payload.user_phone_number,
        payload.interaction_id,
        profile.preferred_language,
        provider="sarvam",
    )
    for turn in payload.interaction_transcript or []:
        text = (turn.indic_text or turn.en_text or "").strip()
        if not text:
            continue
        append_message(
            db,
            profile.id,
            session.conversation_id,
            ConversationMessageCreate(
                role="user" if turn.role == "user" else "assistant",
                message=text,
                language=profile.preferred_language,
                metadata={"provider": "sarvam", "interaction_id": payload.interaction_id},
            ),
        )
    session.status = "completed"
    db.commit()
    record_audit_event(
        db,
        profile.id,
        "voice.sarvam_call_completed",
        resource_type="voice_call_session",
        resource_id=session.id,
        channel="feature_phone",
        metadata={"interaction_id": payload.interaction_id, "app_id": payload.app_id},
    )
    return SarvamWebhookAck(accepted=True, interaction_id=payload.interaction_id, user_id=profile.id, detail="Sarvam call transcript persisted.")


@sarvam_router.post("/browser/turn", response_model=VoiceTurnResponse)
async def handle_browser_audio_turn(
    payload: BrowserVoiceTurnRequest,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> VoiceTurnResponse:
    """Run authenticated browser microphone audio through shared voice AI."""
    try:
        audio = base64.b64decode(payload.audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio is not valid base64.") from exc

    try:
        sarvam = SarvamClient()
        transcript = sarvam.transcribe(audio, payload.audio_mime_type)
        return handle_voice_turn(
            db,
            VoiceTurnRequest(
                call_id=payload.call_id,
                caller_number=profile.phone_number or f"browser-{profile.id}",
                audio_base64=payload.audio_base64,
                audio_mime_type=payload.audio_mime_type,
                idempotency_key=payload.idempotency_key,
            ),
            transcript,
            sarvam,
            profile=profile,
            provider="sarvam",
            synthesize_response=False,
            use_llm=False,
        )
    except SarvamUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@sarvam_router.post("/browser/transcribe", response_model=BrowserVoiceTranscriptResponse)
async def transcribe_browser_audio(
    payload: BrowserVoiceTurnRequest,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> BrowserVoiceTranscriptResponse:
    """Transcribe one browser recording without creating a financial record.

    The access token establishes the current user.  Sarvam only performs
    speech-to-text; transaction extraction, confirmation, and persistence stay
    in the application and authenticated financial APIs.
    """
    del db
    try:
        audio = base64.b64decode(payload.audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio is not valid base64.") from exc

    try:
        transcript = SarvamClient().transcribe(audio, payload.audio_mime_type)
    except SarvamUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return BrowserVoiceTranscriptResponse(
        transcript=transcript.text,
        language=internal_language_code(transcript.language_code, profile.preferred_language or "en"),
        request_id=transcript.request_id,
    )


def _signature_header(
    x_exotel_signature: str | None,
    x_exotel_webhook_signature: str | None,
) -> str | None:
    return x_exotel_signature or x_exotel_webhook_signature


@router.post("/turn", response_model=VoiceTurnResponse)
async def handle_audio_turn(
    payload: VoiceTurnRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    x_exotel_signature: str | None = Header(default=None),
    x_exotel_webhook_signature: str | None = Header(default=None),
) -> VoiceTurnResponse:
    """Process one short Exotel audio turn through the shared web orchestrator."""
    try:
        ExotelClient.from_settings().verify_webhook(
            await request.body(),
            _signature_header(x_exotel_signature, x_exotel_webhook_signature),
        )
        audio = base64.b64decode(payload.audio_base64, validate=True)
    except (ExotelWebhookError, binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        transcript = SarvamClient().transcribe(audio, payload.audio_mime_type)
        return handle_voice_turn(db, payload, transcript, SarvamClient())
    except SarvamUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/webhook", response_model=VoiceTurnResponse | VoiceWebhookAck)
async def handle_exotel_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    x_exotel_signature: str | None = Header(default=None),
    x_exotel_webhook_signature: str | None = Header(default=None),
) -> VoiceTurnResponse | VoiceWebhookAck:
    raw_body = await request.body()
    exotel = ExotelClient.from_settings()
    try:
        exotel.verify_webhook(
            raw_body,
            _signature_header(x_exotel_signature, x_exotel_webhook_signature),
        )
        event = parse_exotel_event(raw_body, request.headers.get("content-type"))
    except ExotelWebhookError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if event.transcript:
        transcript = SpeechTranscript(text=event.transcript, language_code=None, request_id=None)
    else:
        audio: bytes | None = None
        mime_type = event.audio_mime_type
        if event.audio_base64:
            try:
                audio = base64.b64decode(event.audio_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(status_code=400, detail="Exotel audio is not valid base64.") from exc
        elif event.audio_url:
            audio, mime_type = exotel.download_audio(event.audio_url)
        else:
            return VoiceWebhookAck(
                accepted=True,
                call_id=event.call_id,
                detail="Call event acknowledged; no audio turn was included.",
            )

        try:
            transcript = SarvamClient().transcribe(audio, mime_type)
        except SarvamUnavailable as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    try:
        return handle_voice_turn(
            db,
            VoiceTurnRequest(
                call_id=event.call_id,
                caller_number=event.caller_number,
                audio_base64="transcript-only",
                audio_mime_type=event.audio_mime_type,
            ),
            transcript,
            SarvamClient(),
        )
    except SarvamUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
