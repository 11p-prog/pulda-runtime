import os
from pathlib import Path

os.environ["PULDA_DB_PATH"] = "data/test-pulda.db"

from pulda.db import init_db
from pulda.classifier import classify
from pulda.service import create_event, list_events, update_status, build_review, update_event, defer_event, get_event

def setup_module():
    p = Path("data/test-pulda.db")
    if p.exists():
        p.unlink()
    init_db()

def test_classify_family_today():
    c = classify("오늘 어머니께 안부 전화하기")
    assert c.role == "가족"
    assert c.kind == "task_candidate"
    assert c.due_date is not None

def test_event_lifecycle():
    event_id = create_event("오늘 고객 홈페이지 수정하기")
    rows = list_events()
    assert any(r["id"] == event_id for r in rows)
    update_status(event_id, "done")
    done = list_events("done")
    assert any(r["id"] == event_id for r in done)

def test_review():
    result = build_review()
    assert "Daily Review" in result["summary"]

def test_update_event_patches_extended_fields():
    event_id = create_event("프로젝트 견적서 준비하기")
    updated = update_event(event_id, project="Pulda MVP", importance=5)
    assert updated["project"] == "Pulda MVP"
    assert updated["importance"] == 5

def test_defer_event_records_reason_and_next_review():
    event_id = create_event("나중에 다시 검토할 항목")
    deferred = defer_event(event_id, "자료 부족", "2026-08-01")
    assert deferred["status"] == "deferred"
    assert deferred["defer_reason"] == "자료 부족"
    assert deferred["next_review_at"] == "2026-08-01"
    assert get_event(event_id)["status"] == "deferred"
