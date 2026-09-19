import re
from decimal import Decimal, InvalidOperation

from app.conversation.safety_service import (
    no_guarantee_message,
    uncertainty_disclosure,
    unverified_financial_message,
)
from app.conversation.schemas import GeminiResponsePayload, SafetyAssessment

_GUARANTEE_PATTERN = re.compile(
    r"\b(guaranteed|guarantee|guarantees|guaranteeing|risk[- ]?free| निश्चित लाभ|गारंटी|गारंटीड|గ్యారంటీ|ఖచ్చితమైన లాభం)\b",
    flags=re.IGNORECASE,
)
_FINANCIAL_CLAIM_PATTERN = re.compile(
    r"(your|आपकी|आपके|మీ)\s+.{0,30}(balance|savings|income|बचत|आमदनी|बैलेंस|పొదుపు|ఆదాయం|బ్యాలెన్స్)",
    flags=re.IGNORECASE,
)
_AMOUNT_PATTERN = re.compile(r"(?:₹|rs\.?|inr|rupees?)\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?", flags=re.IGNORECASE)
_UNSAFE_ACTION_PATTERN = re.compile(
    r"\b(insert|delete|execute|transfer|send)\b.{0,30}\b(transaction|payment|money|funds|record)\b",
    flags=re.IGNORECASE,
)


def _normalise_amount(value: str) -> str:
    try:
        normalized = format(Decimal(value.replace(",", "")), "f")
    except InvalidOperation:
        return value
    return normalized.rstrip("0").rstrip(".") or "0"


def _amount_tokens(text: str) -> set[str]:
    return {_normalise_amount(token) for token in _AMOUNT_PATTERN.findall(text)}


def validate_response(
    payload: GeminiResponsePayload,
    safety: SafetyAssessment,
    requires_confirmation: bool = False,
    language: str = "en",
    known_financial_values: set[str] | None = None,
) -> GeminiResponsePayload:
    response = " ".join(payload.response.split())
    if not response:
        raise ValueError("The generated response was empty.")
    if safety.risk_level == "high" and safety.guidance:
        response = safety.guidance
    elif _UNSAFE_ACTION_PATTERN.search(response):
        response = (
            "I cannot execute or confirm a financial action from a generated response. "
            "Please review the details and confirm through the secure action provided."
        )
    elif _GUARANTEE_PATTERN.search(response):
        response = (
            f"{no_guarantee_message(language)} "
            f"{uncertainty_disclosure(language)}"
        )
    elif (
        _FINANCIAL_CLAIM_PATTERN.search(response)
        and _amount_tokens(response)
        and not _amount_tokens(response).issubset(
            {_normalise_amount(value) for value in (known_financial_values or set())}
        )
    ):
        response = (
            f"{unverified_financial_message(language)} "
            f"{uncertainty_disclosure(language)}"
        )
    if safety.disclosure_required and uncertainty_disclosure(language) not in response:
        response = f"{response} {uncertainty_disclosure(language)}"
    if requires_confirmation:
        response = (
            f"{response} This is only a pending proposal and has not been recorded yet. "
            "Please confirm before it is saved."
        )
    return payload.model_copy(update={"response": response[:4000]})
