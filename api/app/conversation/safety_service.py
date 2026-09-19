import re

from app.conversation.schemas import SafetyAssessment

_FLAG_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "otp_request",
        (
            r"\botp\b",
            r"one[ -]?time password",
            r"verification code",
            r"share (the )?(code|otp)",
            "ओटीपी",
            "పాస్‌కోడ్",
        ),
    ),
    (
        "credential_request",
        (
            r"\b(password|passcode|pin|cvv|card number|bank details|login)\b",
            r"share (your )?(password|pin|cvv|credentials)",
            "पासवर्ड",
            "पिन",
            "पासकोड",
            "పాస్‌వర్డ్",
            "పిన్",
        ),
    ),
    (
        "urgent_payment_request",
        (
            r"send (the )?money urgently",
            r"urgent (payment|transfer)",
            r"pay (immediately|now)",
            r"transfer (the )?money now",
            "अभी पैसे भेज",
            "तुरंत पैसे",
            "వెంటనే డబ్బు",
            "ఇప్పుడే చెల్లించ",
        ),
    ),
    (
        "fake_bank_call",
        (
            r"(bank|rbi|kyc).{0,45}(call|officer|agent|account blocked|close|suspend)",
            r"(call|officer|agent).{0,45}(bank|rbi|kyc)",
            "बैंक अधिकारी",
            "बैंक का फोन",
            "बैंक वाले",
            "खाता बंद",
            "బ్యాంక్ అధికారి",
            "బ్యాంక్ కాల్",
        ),
    ),
    (
        "suspicious_link",
        (
            r"https?://",
            r"\bwww\.",
            r"\b(bit\.ly|tinyurl\.com|t\.co)/",
            r"click (this )?link",
            "लिंक पर क्लिक",
            "लिंक खोल",
            "లింక్‌పై క్లిక్",
            "లింక్ తెర",
        ),
    ),
    (
        "prize_scam",
        (
            r"\b(prize|lottery|reward|gift)\b",
            r"you (have )?won",
            "इनाम",
            "लॉटरी",
            "पुरस्कार",
            "బహుమతి",
            "లాటరీ",
        ),
    ),
    (
        "guaranteed_returns",
        (
            r"guaranteed (returns?|profit|income)",
            r"risk[- ]?free (returns?|investment)",
            "गारंटी रिटर्न",
            "गारंटीड मुनाफा",
            "గ్యారంటీ రిటర్న్",
            "ఖచ్చితమైన లాభం",
        ),
    ),
    (
        "prompt_injection",
        (
            r"ignore (all )?(previous|prior|above) instructions",
            r"(reveal|show|print) (the )?(system|developer) prompt",
            r"bypass (the )?safety",
            r"jailbreak",
            "पिछले निर्देश भूल",
            "सिस्टम प्रॉम्प्ट दिख",
            "మునుపటి సూచనలను పట్టించుకో",
            "సిస్టమ్ ప్రాంప్ట్ చూప",
        ),
    ),
    ("scam_report", (r"\b(scam|fraud|phishing)\b", "ठगी", "धोखा", "మోసం", "ఫ్రాడ్")),
)

_FINANCIAL_TERMS = (
    "₹",
    "inr",
    "rupee",
    "money",
    "income",
    "expense",
    "saving",
    "budget",
    "loan",
    "interest",
    "investment",
    "return",
    "balance",
    "रुपये",
    "पैसे",
    "बचत",
    "खर्च",
    "आमदनी",
    "డబ్బు",
    "పొదుపు",
    "ఖర్చు",
    "ఆదాయం",
)

_GUIDANCE = {
    "en": "Do not share OTPs, passwords, PINs, or bank details. Do not send money through an unexpected link or caller. Contact your bank using its official number and verify independently.",
    "hi": "OTP, पासवर्ड, PIN या बैंक विवरण साझा न करें। अनजान लिंक या फोन पर पैसे न भेजें। बैंक के आधिकारिक नंबर से खुद जाँच करें।",
    "te": "OTPలు, పాస్‌వర్డ్‌లు, PINలు లేదా బ్యాంక్ వివరాలను పంచుకోవద్దు. తెలియని లింక్ లేదా కాలర్‌కు డబ్బు పంపవద్దు. బ్యాంక్ అధికారిక నంబర్‌తో స్వయంగా నిర్ధారించండి.",
}
_UNCERTAINTY_DISCLOSURE = {
    "en": "I may not have every detail, so please verify important amounts and decisions before acting.",
    "hi": "मेरे पास हर विवरण नहीं हो सकता, इसलिए महत्वपूर्ण रकम और फैसलों पर कार्रवाई से पहले जाँच कर लें।",
    "te": "నా దగ్గర ప్రతి వివరమూ ఉండకపోవచ్చు. ముఖ్యమైన మొత్తాలు మరియు నిర్ణయాలపై చర్య తీసుకునే ముందు దయచేసి పరిశీలించండి.",
}
_NO_GUARANTEE = {
    "en": "I cannot promise a return or outcome.",
    "hi": "मैं किसी रिटर्न या नतीजे का वादा नहीं कर सकता।",
    "te": "నేను ఏ రాబడి లేదా ఫలితాన్నీ వాగ్దానం చేయలేను.",
}
_UNVERIFIED_FINANCIAL = {
    "en": "I do not have enough verified information to state that financial figure.",
    "hi": "उस वित्तीय रकम को तथ्य के रूप में बताने के लिए मेरे पास पर्याप्त सत्यापित जानकारी नहीं है।",
    "te": "ఆ ఆర్థిక మొత్తాన్ని ఖచ్చితమైనదిగా చెప్పడానికి నా దగ్గర తగిన నిర్ధారిత సమాచారం లేదు.",
}


def uncertainty_disclosure(language: str = "en") -> str:
    return _UNCERTAINTY_DISCLOSURE.get(language, _UNCERTAINTY_DISCLOSURE["en"])


def no_guarantee_message(language: str = "en") -> str:
    return _NO_GUARANTEE.get(language, _NO_GUARANTEE["en"])


def unverified_financial_message(language: str = "en") -> str:
    return _UNVERIFIED_FINANCIAL.get(language, _UNVERIFIED_FINANCIAL["en"])


def evaluate_safety(text: str, language: str = "en") -> SafetyAssessment:
    normalized = text.casefold()
    flags = [
        flag
        for flag, patterns in _FLAG_PATTERNS
        if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)
    ]
    high_flags = {"otp_request", "credential_request", "urgent_payment_request", "prompt_injection"}
    risk_level = "high" if high_flags.intersection(flags) else "medium" if flags else "low"
    is_financial = any(term.casefold() in normalized for term in _FINANCIAL_TERMS)
    if flags:
        guidance = _GUIDANCE.get(language, _GUIDANCE["en"])
        if "prompt_injection" in flags:
            guidance = {
                "en": "I can help with your finances, but I cannot reveal or override internal instructions.",
                "hi": "मैं आपकी आर्थिक मदद कर सकता हूँ, लेकिन आंतरिक निर्देश साझा या बदल नहीं सकता।",
                "te": "నేను మీ ఆర్థిక విషయాల్లో సహాయం చేయగలను, కానీ అంతర్గత సూచనలను చూపించలేను లేదా మార్చలేను.",
            }.get(language, "I can help with your finances, but I cannot reveal or override internal instructions.")
        elif "guaranteed_returns" in flags:
            guidance = f"{no_guarantee_message(language)} {uncertainty_disclosure(language)}"
        return SafetyAssessment(
            risk_level=risk_level,
            flags=flags,
            allowed=True,
            # Scam-related input must use deterministic guidance; Gemini is not needed for safety advice.
            allow_llm=False,
            guidance=guidance,
            disclosure_required=True,
        )
    return SafetyAssessment(
        risk_level="low",
        allowed=True,
        allow_llm=True,
        disclosure_required=is_financial,
    )
