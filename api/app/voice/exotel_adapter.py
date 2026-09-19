import hmac
import hashlib
import json
from dataclasses import dataclass
from urllib.parse import parse_qs
import httpx
from app.core.config import get_settings


class ExotelWebhookError(Exception):
    pass


@dataclass
class ExotelEvent:
    call_id: str
    caller_number: str | None = None
    transcript: str | None = None
    audio_base64: str | None = None
    audio_url: str | None = None
    audio_mime_type: str = "audio/wav"


class ExotelClient:
    def __init__(self, webhook_secret: str | None = None):
        self.webhook_secret = webhook_secret

    @classmethod
    def from_settings(cls) -> "ExotelClient":
        settings = get_settings()
        return cls(webhook_secret=settings.exotel_webhook_secret)

    def verify_webhook(self, raw_body: bytes, signature: str | None) -> None:
        if not self.webhook_secret:
            return
        if not signature:
            raise ExotelWebhookError("Missing webhook signature.")
        expected = hmac.new(self.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ExotelWebhookError("Invalid webhook signature.")

    def download_audio(self, url: str) -> tuple[bytes, str]:
        with httpx.Client(timeout=15.0) as client:
            res = client.get(url)
            res.raise_for_status()
            return res.content, res.headers.get("content-type", "audio/wav")


def parse_exotel_event(raw_body: bytes, content_type: str | None) -> ExotelEvent:
    text = raw_body.decode("utf-8", errors="replace")
    if content_type and "application/json" in content_type:
        try:
            data = json.loads(text)
        except Exception as e:
            raise ExotelWebhookError(f"Invalid JSON: {e}") from e
    else:
        parsed = parse_qs(text)
        data = {k: v[0] for k, v in parsed.items()}

    call_id = data.get("CallSid") or data.get("call_id") or data.get("CallSid") or "unknown-call"
    caller_number = data.get("From") or data.get("caller_number") or data.get("caller")
    transcript = data.get("RecordingUrlTranscript") or data.get("transcript")
    audio_url = data.get("RecordingUrl") or data.get("audio_url")
    audio_base64 = data.get("audio_base64")

    return ExotelEvent(
        call_id=call_id,
        caller_number=caller_number,
        transcript=transcript,
        audio_base64=audio_base64,
        audio_url=audio_url,
    )
