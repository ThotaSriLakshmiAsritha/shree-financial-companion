import json
import logging
import re
from typing import Any

import httpx

from app.conversation.schemas import GeminiResponsePayload
from app.core.config import Settings, get_settings
from app.core.metrics import observe_duration

logger = logging.getLogger(__name__)


class GeminiUnavailable(RuntimeError):
    """Raised when Gemini cannot be used for this request."""


class GeminiClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @observe_duration("llm.gemini")
    def generate_response(
        self,
        *,
        user_message: str,
        intent: str,
        extracted_entities: str,
        personalization: str,
    ) -> GeminiResponsePayload:
        api_key = self.settings.gemini_api_key
        if not api_key:
            raise GeminiUnavailable("Gemini API key is not configured.")

        endpoint = (
            f"{self.settings.gemini_base_url.rstrip('/')}/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        system_instruction = (
            "You are Sahachari, a careful multilingual financial companion. "
            "Return only valid JSON with this shape: "
            '{"response":"string","suggested_next_step":"string or null",'
            '"asks_confirmation":true or false}. '
            "Do not claim a financial transaction was saved. A pending proposal must be confirmed by the user. "
            "Use simple, respectful language and never invent values outside the supplied context. "
            "Never guarantee returns, profit, approval, or any financial outcome. State uncertainty when details "
            "are missing, and do not request OTPs, passwords, PINs, CVV, or bank credentials."
        )
        user_prompt = (
            f"{personalization}\n\n"
            f"DETECTED INTENT: {intent}\n"
            f"EXTRACTED ENTITIES: {extracted_entities}\n"
            f"USER INPUT: {user_message}\n\n"
            "Write the helpful response now. If a transaction proposal is present, ask for explicit confirmation."
        )
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
        }
        try:
            response = httpx.post(
                endpoint,
                params={"key": api_key},
                json=body,
                timeout=self.settings.gemini_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Gemini response generation failed: %s", exc)
            raise GeminiUnavailable("Gemini response generation failed.") from exc

        try:
            payload = response.json()
            raw_text = payload["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_payload(raw_text)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Gemini returned an invalid structured response: %s", exc)
            raise GeminiUnavailable("Gemini returned an invalid response.") from exc

    @staticmethod
    def _parse_payload(raw_text: str) -> GeminiResponsePayload:
        cleaned = raw_text.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            cleaned = fenced.group(1)
        parsed = json.loads(cleaned)
        if isinstance(parsed, str):
            parsed = {"response": parsed}
        return GeminiResponsePayload.model_validate(parsed)
