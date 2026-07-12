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


def date_label(iso_date: str, today: date | None = None) -> str:
    """Human, log-like label for a calendar date relative to "today" (KST).

    오늘 / 어제 / "N일 전" (within a week) / "M월 D일" (older) — matches how a
    person naturally recalls dates, per the CR-0009 activity-log redesign.
    """
    today = today or today_kst()
    d = date.fromisoformat(iso_date)
    diff = (today - d).days
    if diff == 0:
        return "오늘"
    if diff == 1:
        return "어제"
    if 2 <= diff <= 6:
        return f"{diff}일 전"
    return f"{d.month}월 {d.day}일"
