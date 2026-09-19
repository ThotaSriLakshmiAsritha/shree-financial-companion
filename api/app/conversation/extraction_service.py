import re
from datetime import date, timedelta
from decimal import Decimal

from app.core.time import local_today
from app.conversation.schemas import ExtractedTransaction, Intent

_AMOUNT_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr|rupees?)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)|"
    r"(?<![\w])([0-9][0-9,]*(?:\.[0-9]{1,2})?)(?:\s*(?:₹|rs\.?|inr|rupees?))?",
    re.IGNORECASE,
)
_DATE_PATTERN = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b|\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_MONTH_PATTERN = re.compile(
    r"\b(?:on\s+)?(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.IGNORECASE,
)
_MONTHS = {
    name.lower(): index
    for index, name in enumerate(
        ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
        start=1,
    )
}
_CATEGORY_TERMS = {
    "school": "education",
    "fees": "education",
    "books": "education",
    "food": "food",
    "groceries": "food",
    "rent": "housing",
    "bus": "transport",
    "travel": "transport",
    "medicine": "health",
    "loan": "debt",
}


def _parse_amount(message: str) -> Decimal | None:
    matches = list(_AMOUNT_PATTERN.finditer(message))
    if not matches:
        return None
    raw = next((match.group(1) or match.group(2) for match in matches if match.group(1)), None)
    if raw is None:
        raw = matches[0].group(1) or matches[0].group(2)
    return Decimal(raw.replace(",", ""))


def _parse_date(message: str, today: date) -> date:
    normalized = message.casefold()
    if "day before yesterday" in normalized:
        return today - timedelta(days=2)
    if "yesterday" in normalized or "कल" in normalized or "నిన్న" in normalized:
        return today - timedelta(days=1)
    if "tomorrow" in normalized or "कल" in normalized and "spent" not in normalized:
        return today + timedelta(days=1)
    if "today" in normalized or "आज" in normalized or "ఈ రోజు" in normalized:
        return today

    match = _DATE_PATTERN.search(message)
    if match:
        if match.group(4):
            return date(int(match.group(4)), int(match.group(5)), int(match.group(6)))
        year = int(match.group(3))
        year += 2000 if year < 100 else 0
        return date(year, int(match.group(2)), int(match.group(1)))

    month_match = _MONTH_PATTERN.search(message)
    if month_match:
        return date(today.year, _MONTHS[month_match.group(2).casefold()], int(month_match.group(1)))
    return today


def _parse_transaction_type(message: str) -> str | None:
    normalized = message.casefold()
    if any(term in normalized for term in ("saved", "saving", "set aside", "kept", "బచत", "बचत", "దాచ")):
        return "saving"
    if any(term in normalized for term in ("earned", "income", "salary", "got paid", "कमाया", "సంపాదించ")):
        return "income"
    if any(term in normalized for term in ("spent", "spend", "paid", "bought", "expense", "खर्च", "ఖర్చు")):
        return "expense"
    return None


def _parse_currency(message: str) -> str:
    normalized = message.casefold()
    if "$" in message or "usd" in normalized or "dollar" in normalized:
        return "USD"
    return "INR"


def _parse_category(message: str) -> str | None:
    normalized = message.casefold()
    return next((category for term, category in _CATEGORY_TERMS.items() if term in normalized), None)


def extract_transaction(
    message: str,
    intent: Intent,
    source: str,
    today: date | None = None,
) -> ExtractedTransaction | None:
    if intent is not Intent.LOG_TRANSACTION:
        return None
    amount = _parse_amount(message)
    transaction_type = _parse_transaction_type(message)
    if amount is None or transaction_type is None:
        return None

    category = _parse_category(message)
    return ExtractedTransaction(
        transaction_type=transaction_type,
        amount=amount,
        currency=_parse_currency(message),
        category=category,
        description=message[:500],
        date=_parse_date(message, today or local_today()),
        source=source,
        confidence=Decimal("0.90"),
        raw_statement=message[:2000],
    )
