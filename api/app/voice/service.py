import base64
import logging
from uuid import UUID, uuid4
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Profile
from app.auth.service import normalize_phone_number
from app.context.models import Conversation, ConversationMessage
from app.context.schemas import ConversationMessageCreate
from app.conversation.orchestrator import ConversationOrchestrator
from app.conversation.schemas import ConversationMessageRequest, LanguageCode
from app.voice.models import VoiceCallSession
from app.voice.sarvam_client import SarvamClient, SpeechAudio, SpeechTranscript, internal_language_code, sarvam_language_code
from app.voice.schemas import VoiceTurnRequest, VoiceTurnResponse

logger = logging.getLogger(__name__)


def get_voice_profile(db: Session, phone_number: str) -> Profile:
    normalized = normalize_phone_number(phone_number)
    profile = None
    if normalized:
        profile = db.scalar(select(Profile).where(Profile.phone_number == normalized))
    if not profile:
        profile = db.scalar(select(Profile).where(Profile.phone_number == phone_number))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile associated with this phone number.",
        )
    return profile


def get_or_create_voice_session(
    db: Session,
    user_id: UUID,
    phone_number: str,
    external_call_id: str,
    language: str,
    provider: str = "exotel",
) -> VoiceCallSession:
    session = db.scalar(
        select(VoiceCallSession).where(
            VoiceCallSession.provider == provider,
            VoiceCallSession.external_call_id == external_call_id,
        )
    )
    if session:
        return session

    conversation = Conversation(
        user_id=user_id,
        channel="feature_phone" if provider != "browser" else "web",
        language=language,
    )
    db.add(conversation)
    db.flush()

    session = VoiceCallSession(
        user_id=user_id,
        provider=provider,
        external_call_id=external_call_id,
        phone_number=phone_number,
        conversation_id=conversation.id,
        language=language,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def handle_voice_turn(
    db: Session,
    request: VoiceTurnRequest,
    transcript: SpeechTranscript,
    voice: SarvamClient,
    orchestrator: ConversationOrchestrator | None = None,
    profile: Profile | None = None,
    provider: str = "exotel",
    synthesize_response: bool = True,
    use_llm: bool = True,
) -> VoiceTurnResponse:
    if profile is None:
        if not request.caller_number:
            raise HTTPException(status_code=400, detail="Caller number required")
        profile = get_voice_profile(db, request.caller_number)

    lang_code = profile.preferred_language or "te"
    session = get_or_create_voice_session(
        db,
        profile.id,
        request.caller_number or profile.phone_number or "unknown",
        request.call_id,
        lang_code,
        provider=provider,
    )

    if orchestrator is None:
        orchestrator = ConversationOrchestrator(use_llm=use_llm)

    # Process turn with orchestrator
    result = orchestrator.handle(
        db,
        profile,
        ConversationMessageRequest(
            message=transcript.text,
            conversation_id=session.conversation_id,
            channel="feature_phone" if provider != "browser" else "voice",
            language=LanguageCode(lang_code) if lang_code in {"en", "hi", "te"} else None,
        ),
    )

    response_text = result.response or "Done"
    audio_base64 = ""
    if synthesize_response and response_text:
        audio = voice.synthesize(response_text, sarvam_language_code(lang_code))
        audio_base64 = base64.b64encode(audio.audio).decode("ascii")

    proposal_id = result.transaction_proposal.id if result.transaction_proposal else None

    return VoiceTurnResponse(
        user_id=profile.id,
        conversation_id=session.conversation_id,
        language=result.language,
        response_audio_base64=audio_base64,
        transcript=transcript.text,
        proposal_id=proposal_id,
    )
