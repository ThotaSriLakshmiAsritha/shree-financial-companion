from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

APPLICATION_TIMEZONE_NAME = "Asia/Kolkata"
APPLICATION_TIMEZONE = ZoneInfo(APPLICATION_TIMEZONE_NAME)


def utc_now() -> datetime:
    """Return an aware UTC timestamp for storage and audit fields."""
    return datetime.now(timezone.utc)


def local_today() -> date:
    """Return today's date in the application's user-facing timezone."""
    return datetime.now(APPLICATION_TIMEZONE).date()
