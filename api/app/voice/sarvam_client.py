from dataclasses import dataclass
import base64
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SpeechAudio:
    audio: bytes
    mime_type: str = "audio/wav"
    request_id: str | None = None


@dataclass
class SpeechTranscript:
    text: str
    language_code: str | None = None
    request_id: str | None = None


class SarvamUnavailable(Exception):
    pass


def internal_language_code(code: str | None, fallback: str = "en") -> str:
    if not code:
        return fallback
    code_lower = code.lower()
    if code_lower.startswith("te"):
        return "te"
    if code_lower.startswith("hi"):
        return "hi"
    return "en"


def sarvam_language_code(code: str | None) -> str:
    if not code:
        return "en-IN"
    code_lower = code.lower()
    if code_lower.startswith("te"):
        return "te-IN"
    if code_lower.startswith("hi"):
        return "hi-IN"
    return "en-IN"


class SarvamClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> SpeechTranscript:
        if not self.settings.sarvam_api_key:
            return SpeechTranscript(text="₹200 spent on groceries", language_code="en-IN", request_id="mock-1")
        try:
            url = f"{self.settings.sarvam_base_url.rstrip('/')}/speech-to-text"
            files = {"file": ("audio.wav", audio_bytes, mime_type)}
            data = {"model": self.settings.sarvam_stt_model, "mode": self.settings.sarvam_stt_mode}
            headers = {"api-subscription-key": self.settings.sarvam_api_key}
            with httpx.Client(timeout=self.settings.sarvam_timeout_seconds) as client:
                res = client.post(url, files=files, data=data, headers=headers)
                res.raise_for_status()
                payload = res.json()
                return SpeechTranscript(
                    text=payload.get("transcript", ""),
                    language_code=payload.get("language_code", "en-IN"),
                    request_id=payload.get("request_id"),
                )
        except Exception as exc:
            logger.warning("Sarvam transcribe failed: %s", exc)
            raise SarvamUnavailable(f"Sarvam speech service error: {exc}") from exc

    def synthesize(self, text: str, language_code: str = "te-IN") -> SpeechAudio:
        if not self.settings.sarvam_api_key:
            return SpeechAudio(audio=b"RIFFmockaudio", mime_type="audio/wav", request_id="mock-tts")
        try:
            url = f"{self.settings.sarvam_base_url.rstrip('/')}/text-to-speech"
            headers = {
                "api-subscription-key": self.settings.sarvam_api_key,
                "Content-Type": "application/json",
            }
            body = {
                "inputs": [text],
                "target_language_code": language_code,
                "speaker": self.settings.sarvam_tts_speaker,
                "model": self.settings.sarvam_tts_model,
            }
            with httpx.Client(timeout=self.settings.sarvam_timeout_seconds) as client:
                res = client.post(url, json=body, headers=headers)
                res.raise_for_status()
                payload = res.json()
                audios = payload.get("audios", [])
                if audios:
                    return SpeechAudio(audio=base64.b64decode(audios[0]), mime_type="audio/wav")
                return SpeechAudio(audio=b"", mime_type="audio/wav")
        except Exception as exc:
            logger.warning("Sarvam synthesize failed: %s", exc)
            raise SarvamUnavailable(f"Sarvam TTS error: {exc}") from exc
