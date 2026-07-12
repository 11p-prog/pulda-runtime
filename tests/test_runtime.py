import os
from pathlib import Path

os.environ["PULDA_DB_PATH"] = "data/test-pulda.db"

from datetime import datetime

from pulda.db import init_db
from pulda.classifier import classify
from pulda.service import (
    create_event, list_events, update_status, build_review, update_event, defer_event,
    get_event, delete_event, context_workspace, add_attachment, group_events_by_date,
)
from pulda.timeutil import date_label, today_kst
from datetime import timedelta

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

def test_scheduled_at_matches_due_date_for_relative_day():
    # CR-0007 audit finding #9: "내일 오후 3시" previously produced
    # due_date=tomorrow but scheduled_at=today 15:00 — a self-contradictory
    # record. scheduled_at must land on the same calendar day as due_date.
    c = classify("내일 오후 3시 병원 방문")
    assert c.due_date is not None
    assert c.scheduled_at is not None
    assert c.scheduled_at[:10] == c.due_date
    assert c.scheduled_at[11:13] == "15"

def test_delete_event_removes_event_and_attachments():
    event_id = create_event("삭제될 이벤트")
    add_attachment(event_id, "test.pdf", "stored123.pdf", "application/pdf", 100)
    delete_event(event_id)
    assert get_event(event_id) is None

def test_context_workspace_scopes_to_selected_historical_date():
    # CR-0002/CR-0003 audit findings #1/#2: a historical date must show only
    # that day's events/recent list — not the whole context, and not a
    # rolling "last N regardless of date" fallback.
    today_event_id = create_event("오늘 생성된 이벤트")
    today_row = get_event(today_event_id)
    other_day = "2020-01-01"
    with_other_date = dict(today_row)
    # Simulate a record actually created on a different day by checking the
    # workspace scoping logic directly against a date nothing was created on.
    workspace = context_workspace("today", selected_date=other_day)
    assert all(e["created_at"][:10] == other_day for e in workspace["events"])
    assert all(e["created_at"][:10] == other_day for e in workspace["recent"])
    assert workspace["recent"] == []  # nothing was created on other_day
    assert workspace["events"] == []

def test_capture_rejects_disallowed_file_type_and_rolls_back_event():
    # CR-0007 audit findings #3/#4: server must validate file type itself
    # (UI `accept` is not a security boundary), and a rejected upload must
    # not leave an orphan Event behind.
    from fastapi.testclient import TestClient
    from pulda.app import app

    client = TestClient(app)
    before = len(list_events(limit=1000))
    resp = client.post(
        "/capture",
        data={"text": "악성 파일 첨부 테스트", "ctx": "today"},
        files={"file": ("evil.html", b"<script>alert(1)</script>", "text/html")},
    )
    assert resp.status_code == 400
    after = len(list_events(limit=1000))
    assert after == before  # no orphan Event created

def test_download_attachment_sets_security_headers():
    from fastapi.testclient import TestClient
    from pulda.app import app

    client = TestClient(app)
    resp = client.post(
        "/capture",
        data={"text": "정상 파일 첨부 테스트", "ctx": "today"},
        files={"file": ("doc.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    assert resp.status_code in (200, 303)
    events = [e for e in list_events(limit=1000) if e["text"] == "정상 파일 첨부 테스트"]
    assert events, "event should have been created"
    event_id = events[0]["id"]
    from pulda.service import list_attachments
    attachments = list_attachments(event_id)
    assert attachments, "attachment should have been saved"
    dl = client.get(f"/attachments/{attachments[0]['id']}")
    assert dl.status_code == 200
    assert dl.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in dl.headers["content-disposition"]

def test_date_label_relative_wording():
    # CR-0009: the "전체 Event" log must read like an activity log
    # (오늘/어제/N일 전), not a flat pile of undated rows.
    today = today_kst()
    assert date_label(today.isoformat(), today) == "오늘"
    assert date_label((today - timedelta(days=1)).isoformat(), today) == "어제"
    assert date_label((today - timedelta(days=3)).isoformat(), today) == "3일 전"
    old = today - timedelta(days=30)
    assert date_label(old.isoformat(), today) == f"{old.month}월 {old.day}일"

def test_group_events_by_date_buckets_and_preserves_order():
    events = [
        {"id": 1, "created_at": "2026-07-12T16:08:00"},
        {"id": 2, "created_at": "2026-07-12T15:32:00"},
        {"id": 3, "created_at": "2026-07-11T09:21:00"},
    ]
    groups = group_events_by_date(events)
    assert [g["date"] for g in groups] == ["2026-07-12", "2026-07-11"]
    assert [e["id"] for e in groups[0]["events"]] == [1, 2]
    assert [e["id"] for e in groups[1]["events"]] == [3]
