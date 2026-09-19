from decimal import Decimal

from app.conversation.schemas import Intent, IntentDetectionResult

_INTENT_TERMS: tuple[tuple[Intent, tuple[str, ...], Decimal], ...] = (
    (
        Intent.SCAM_REPORT,
        (
            "scam",
            "fraud",
            "otp",
            "one time password",
            "password",
            "pin",
            "suspicious",
            "fake",
            "prize",
            "lottery",
            "reward",
            "urgent payment",
            "send money",
            "bank call",
            "kyc",
            "link",
            "ठगी",
            "इनाम",
            "लॉटरी",
            "तुरंत पैसे",
            "बैंक",
            "लिंक",
            "మోసం",
            "బహుమతి",
            "లాటరీ",
            "వెంటనే డబ్బు",
            "బ్యాంక్",
            "లింక్",
        ),
        Decimal("0.98"),
    ),
    (
        Intent.LOG_TRANSACTION,
        (
            "spent",
            "spend",
            "paid",
            "bought",
            "expense",
            "earned",
            "income",
            "salary",
            "saved",
            "saving",
            "set aside",
            "खर्च",
            "कमाया",
            "बचत",
            "ఖర్చు",
            "సంపాదించ",
            "దాచ",
        ),
        Decimal("0.92"),
    ),
    (
        Intent.CHECK_BALANCE,
        ("balance", "savings", "how much do i have", "నా పొదుపు", "बचत कितनी", "कितना बचा"),
        Decimal("0.90"),
    ),
    (
        Intent.CREATE_GOAL,
        ("goal", "target", "save for", "want to buy", "लक्ष्य", "लक्ष्य के लिए", "లక్ష్యం", "కొనాలి"),
        Decimal("0.88"),
    ),
    (
        Intent.LEARN_CONCEPT,
        (
            "explain",
            "what is",
            "how does",
            "learn",
            "understand",
            "teach me",
            "समझाइए",
            "అర్థం",
            "నేర్చుకోవాలి",
        ),
        Decimal("0.86"),
    ),
    (
        Intent.FINANCIAL_QUESTION,
        (
            "loan",
            "interest",
            "budget",
            "debt",
            "emi",
            "credit",
            "investment",
            "return",
            "profit",
            "guaranteed",
            "कर्ज",
            "ब्याज",
            "రుణం",
            "వడ్డీ",
        ),
        Decimal("0.82"),
    ),
)


def detect_intent(text: str) -> IntentDetectionResult:
    normalized = text.casefold()
    for intent, terms, confidence in _INTENT_TERMS:
        matched = [term for term in terms if term.casefold() in normalized]
        if matched:
            return IntentDetectionResult(intent=intent, confidence=confidence, matched_terms=matched[:5])
    return IntentDetectionResult(intent=Intent.GENERAL_CONVERSATION, confidence=Decimal("0.55"))
