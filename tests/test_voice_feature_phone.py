import base64
from uuid import uuid4

from app.auth.models import Profile
from app.context.models import Conversation, ConversationMessage
from app.conversation.gemini_client import GeminiClient
from app.conversation.orchestrator import ConversationOrchestrator
from app.conversation.schemas import GeminiResponsePayload
from app.db.base import Base
from app.financial.models import Transaction, TransactionProposal
from app.voice.models import VoiceCallSession
from app.voice.sarvam_client import SpeechAudio, SpeechTranscript
from app.voice.schemas import VoiceTurnRequest
from app.voice.service import handle_voice_turn
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


class FakeSarvamClient:
    def synthesize(self, text: str, language_code: str) -> SpeechAudio:
        return SpeechAudio(audio=b"RIFF-test-audio", mime_type="audio/wav", request_id="tts-1")


class FakeGeminiClient(GeminiClient):
    def __init__(self) -> None:
        pass

    def generate_response(self, **kwargs: str) -> GeminiResponsePayload:
        return GeminiResponsePayload(response="I heard you. Please confirm this pending update.")


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_feature_phone_uses_same_user_conversation_and_proposal_workflow() -> None:
    db = make_session()
    user_id = uuid4()
    db.add(
        Profile(
            id=user_id,
            phone_number="+919876543210",
            preferred_language="te",
            display_name="Lakshmi",
        )
    )
    db.commit()

    result = handle_voice_turn(
        db,
        VoiceTurnRequest(
            call_id="exo-call-1",
            caller_number="+91 98765 43210",
            audio_base64=base64.b64encode(b"audio").decode(),
        ),
        SpeechTranscript(
            text="I spent ₹250 on school books",
            language_code="te-IN",
            request_id="stt-1",
        ),
        FakeSarvamClient(),
        ConversationOrchestrator(FakeGeminiClient()),
    )

    session = db.scalar(select(VoiceCallSession).where(VoiceCallSession.external_call_id == "exo-call-1"))
    conversation = db.get(Conversation, result.conversation_id)
    proposal = db.scalar(select(TransactionProposal).where(TransactionProposal.user_id == user_id))

    assert result.user_id == user_id
    assert result.language.value == "te"
    assert result.response_audio_base64 == base64.b64encode(b"RIFF-test-audio").decode()
    assert session is not None
    assert session.user_id == user_id
    assert conversation is not None
    assert conversation.user_id == user_id
    assert conversation.channel == "feature_phone"
    assert proposal is not None
    assert proposal.status == "pending"
    assert db.scalar(select(Transaction).where(Transaction.user_id == user_id)) is None
    assert db.scalar(
        select(ConversationMessage).where(
            ConversationMessage.conversation_id == result.conversation_id,
            ConversationMessage.role == "user",
        )
    ) is not None


def test_same_exotel_call_id_reuses_conversation() -> None:
    db = make_session()
    user_id = uuid4()
    db.add(Profile(id=user_id, phone_number="+919876543210", preferred_language="en"))
    db.commit()
    voice = FakeSarvamClient()
    orchestrator = ConversationOrchestrator(FakeGeminiClient())
    request = VoiceTurnRequest(
        call_id="exo-call-2",
        caller_number="+919876543210",
        audio_base64="audio",
    )
    first = handle_voice_turn(
        db,
        request,
        SpeechTranscript(text="Hello", language_code="en-IN", request_id=None),
        voice,
        orchestrator,
    )
    second = handle_voice_turn(
        db,
        request,
        SpeechTranscript(text="Tell me more", language_code="en-IN", request_id=None),
        voice,
        orchestrator,
    )

    assert first.conversation_id == second.conversation_id
    assert db.query(VoiceCallSession).count() == 1
    assert db.query(Conversation).count() == 1
