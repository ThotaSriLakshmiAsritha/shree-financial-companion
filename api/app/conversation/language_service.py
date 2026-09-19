import re
from decimal import Decimal

from app.conversation.schemas import LanguageCode, LanguageDetectionResult

_TELUGU = re.compile(r"[\u0c00-\u0c7f]")
_DEVANAGARI = re.compile(r"[\u0900-\u097f]")
_LATIN = re.compile(r"[a-zA-Z]")


def detect_language(text: str, preferred: LanguageCode | str = LanguageCode.ENGLISH) -> LanguageDetectionResult:
    """Use script detection first, then the saved profile language as fallback."""
    if _TELUGU.search(text):
        return LanguageDetectionResult(language=LanguageCode.TELUGU, confidence=Decimal("0.98"), method="script")
    if _DEVANAGARI.search(text):
        return LanguageDetectionResult(language=LanguageCode.HINDI, confidence=Decimal("0.98"), method="script")
    if _LATIN.search(text):
        return LanguageDetectionResult(language=LanguageCode.ENGLISH, confidence=Decimal("0.82"), method="latin_script")
    return LanguageDetectionResult(language=LanguageCode(preferred), confidence=Decimal("0.50"), method="profile_fallback")
