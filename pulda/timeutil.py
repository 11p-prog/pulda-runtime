"""Central time source for Pulda.

The container clock runs in UTC, but the user is in Korea (KST, UTC+9).
Using naive `datetime.now()` / `date.today()` means "today" flips over at
09:00 KST instead of midnight KST — for roughly 9 hours a day the app
thinks it's still yesterday from the user's point of view. All "what day
is it" / "what time is it" logic must go through this module instead of
calling `datetime`/`date` directly.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """Current wall-clock time in Korea, as a naive datetime (KST implied)."""
    return datetime.now(KST).replace(tzinfo=None)


def today_kst() -> date:
    """Current calendar date in Korea."""
    return now_kst().date()
