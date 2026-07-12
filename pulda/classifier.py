from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from .timeutil import now_kst

@dataclass
class Classification:
    role: str
    area: str
    kind: str
    urgency: int
    importance: int
    status: str
    due_date: str | None = None
    scheduled_at: str | None = None

ROLE_KEYWORDS = {
    "가족": ["아들", "아이", "아내", "부모", "어머니", "아버지", "장모", "가족"],
    "회사": ["고객", "홈페이지", "워드프레스", "프로젝트", "계약", "견적", "매출", "풀다", "a4u"],
    "성당": ["성당", "본당", "교구", "사목", "총회장", "신부", "미사"],
    "개인": ["병원", "치과", "운동", "공부", "책", "건강", "개인"],
}
AREA_KEYWORDS = {
    "재무": ["돈", "매출", "비용", "결제", "환불", "견적", "계약"],
    "건강": ["병원", "치과", "운동", "통증", "약", "건강"],
    "관계": ["연락", "전화", "안부", "만남", "가족"],
    "학습": ["공부", "책", "강의", "교육", "코스", "연구"],
    "프로젝트": ["프로젝트", "개발", "수정", "디자인", "홈페이지", "배포"],
    "운영": ["회의", "보고", "정리", "검토", "준비", "운영"],
}

def _pick(text: str, mapping: dict[str, list[str]], default: str) -> str:
    for key, words in mapping.items():
        if any(word in text for word in words):
            return key
    return default

def classify(text: str, now: datetime | None = None) -> Classification:
    now = now or now_kst()
    role = _pick(text, ROLE_KEYWORDS, "개인")
    area = _pick(text, AREA_KEYWORDS, "운영")
    kind = "event"
    if any(x in text for x in ["해야", "하기", "제출", "보내", "확인", "수정", "연락"]):
        kind = "task_candidate"
    if any(x in text for x in ["회의", "예약", "미사", "오전", "오후", "시", "방문"]):
        kind = "scheduled_event"

    urgency = 2
    importance = 2
    if any(x in text for x in ["긴급", "즉시", "오늘", "당장", "마감"]):
        urgency = 4
    if any(x in text for x in ["가족", "건강", "매출", "계약", "납기", "성당 행사"]):
        importance = 4
    if "나중" in text or "언젠가" in text:
        urgency = 1

    due_date = None
    if "오늘" in text:
        due_date = now.date().isoformat()
    elif "내일" in text:
        due_date = (now.date() + timedelta(days=1)).isoformat()

    scheduled_at = None
    m = re.search(r"(오전|오후)?\s*(\d{1,2})시", text)
    if m:
        hour = int(m.group(2))
        if m.group(1) == "오후" and hour < 12:
            hour += 12
        scheduled_at = now.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()

    return Classification(
        role=role, area=area, kind=kind, urgency=urgency,
        importance=importance, status="inbox",
        due_date=due_date, scheduled_at=scheduled_at,
    )
