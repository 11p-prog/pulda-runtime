import os
from pathlib import Path

os.environ["PULDA_DB_PATH"] = "data/test-pulda.db"

from datetime import datetime

from pulda.db import init_db
from pulda.classifier import classify
from pulda.service import (
    create_event, list_events, update_status, build_review, update_event, defer_event,
    get_event, delete_event, soft_delete_event, context_workspace, add_attachment, group_events_by_date,
    context_events, distinct_projects,
    interpret_event, correct_interpretation, record_outcome, propose_follow_up,
    capture_knowledge_source, find_relevant_knowledge,
    capture_daily_activity, get_daily_activity,
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

def test_first_living_loop_reuses_human_correction():
    first_event_id = create_event("VIP 고객 홈페이지 검토")
    first_interpretation = interpret_event(first_event_id)
    assert first_interpretation["role"] == "회사"
    assert first_interpretation["source_evidence"] == f"event:{first_event_id}:original"
    assert first_interpretation["model"] == "rule-based-v0"

    correction = correct_interpretation(
        first_interpretation["id"],
        field_name="importance",
        new_value="5",
        rationale="VIP 고객 요청은 최우선 검토",
        scope="reusable",
        reusable_match_text="VIP",
    )
    assert correction["scope"] == "reusable"
    assert correction["rule_id"] is not None

    outcome = record_outcome(first_event_id, "요구사항 확인 완료")
    follow_up = propose_follow_up(first_event_id, outcome["id"], "견적 범위를 확정한다")
    assert follow_up["status"] == "proposed"

    next_event_id = create_event("VIP 신규 문의 회신")
    next_interpretation = interpret_event(next_event_id)
    assert next_interpretation["importance"] == 5
    assert correction["rule_id"] in next_interpretation["applied_rule_ids"]
    assert get_event(next_event_id)["text"] == "VIP 신규 문의 회신"

def test_living_loop_is_executable_through_api():
    from fastapi.testclient import TestClient
    from pulda.app import app

    client = TestClient(app)
    first = client.post("/api/events", json={"text": "API우선 고객 요구사항 확인"})
    assert first.status_code == 200
    first_event_id = first.json()["id"]

    interpreted = client.post(
        f"/api/events/{first_event_id}/interpretations",
        json={"confidence": 0.8},
    )
    assert interpreted.status_code == 200
    interpretation = interpreted.json()
    assert interpretation["source_evidence"] == f"event:{first_event_id}:original"

    corrected = client.post(
        f"/api/interpretations/{interpretation['id']}/corrections",
        json={
            "field_name": "importance",
            "new_value": "5",
            "rationale": "API우선 고객은 최우선으로 검토한다",
            "scope": "reusable",
            "reusable_match_text": "API우선",
        },
    )
    assert corrected.status_code == 200
    rule_id = corrected.json()["rule_id"]

    outcome = client.post(
        f"/api/events/{first_event_id}/outcomes",
        json={"result_text": "요구사항 확인 완료"},
    )
    assert outcome.status_code == 200
    follow_up = client.post(
        f"/api/events/{first_event_id}/follow-ups",
        json={"outcome_id": outcome.json()["id"], "text": "견적 범위를 확정한다"},
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["status"] == "proposed"

    second = client.post("/api/events", json={"text": "API우선 신규 문의 회신"})
    second_event_id = second.json()["id"]
    next_interpretation = client.post(
        f"/api/events/{second_event_id}/interpretations", json={}
    )
    assert next_interpretation.status_code == 200
    assert next_interpretation.json()["importance"] == 5
    assert rule_id in next_interpretation.json()["applied_rule_ids"]

def test_daily_activity_capture_is_date_scoped_idempotent_and_portable():
    payload = {
        "activity_date": "2026-07-18",
        "source_channel": "chatgpt",
        "external_key": "chatgpt:primary:2026-07-18",
        "source_coverage": "connected project conversations and approved Notion records",
        "access_gaps": "some unrelated conversations unavailable",
        "privacy_reviewed": True,
        "items": [
            {
                "item_type": "decision",
                "project": "PRJ-PULDA-OS",
                "summary": "22:30을 일일 운영 종료 기준으로 사용한다.",
                "source_ref": "notion:CR-0015",
                "review_state": "register",
            },
            {
                "item_type": "hold",
                "project": "PRJ-PULDA-OS",
                "summary": "Runtime 직접 등록 어댑터 검증이 남아 있다.",
                "review_state": "record_only",
            },
        ],
    }
    first = capture_daily_activity(**payload)
    assert first["created"] is True
    assert first["added_count"] == 2
    assert first["event"]["source"] == "daily_activity:chatgpt"
    assert first["event"]["project"] == "PRJ-PULDA-OS"

    repeated = capture_daily_activity(**payload)
    assert repeated["created"] is False
    assert repeated["added_count"] == 0
    assert repeated["event"]["id"] == first["event"]["id"]
    assert len(repeated["items"]) == 2

    exported = get_daily_activity("2026-07-18", "chatgpt")
    assert exported["batch"]["external_key"] == payload["external_key"]
    assert exported["batch"]["source_coverage"] == payload["source_coverage"]
    assert {item["item_type"] for item in exported["items"]} == {"decision", "hold"}

def test_daily_activity_api_returns_event_id_and_rejects_invalid_items():
    from fastapi.testclient import TestClient
    from pulda.app import app

    client = TestClient(app)
    payload = {
        "activity_date": "2026-07-19",
        "source_channel": "chatgpt",
        "external_key": "chatgpt:primary:2026-07-19",
        "privacy_reviewed": True,
        "items": [{"item_type": "work_result", "summary": "일일 활동 API 테스트 완료"}],
    }
    created = client.post("/api/daily-activities", json=payload)
    assert created.status_code == 200
    assert created.json()["event"]["id"] > 0
    assert created.json()["added_count"] == 1

    fetched = client.get("/api/daily-activities/2026-07-19")
    assert fetched.status_code == 200
    assert fetched.json()["event"]["id"] == created.json()["event"]["id"]

    invalid = dict(payload)
    invalid["activity_date"] = "2026-07-20"
    invalid["external_key"] = "chatgpt:primary:2026-07-20"
    invalid["items"] = [{"item_type": "private_secret", "summary": "저장 금지"}]
    rejected = client.post("/api/daily-activities", json=invalid)
    assert rejected.status_code == 400
    assert get_daily_activity("2026-07-20", "chatgpt") is None

def test_daily_activity_requires_privacy_review_and_configured_token():
    from fastapi.testclient import TestClient
    from pulda.app import app
    from pulda.config import settings

    client = TestClient(app)
    payload = {
        "activity_date": "2026-07-21",
        "source_channel": "chatgpt",
        "external_key": "chatgpt:primary:2026-07-21",
        "privacy_reviewed": False,
        "items": [{"item_type": "decision", "summary": "민감정보 검토 전 후보"}],
    }
    not_reviewed = client.post("/api/daily-activities", json=payload)
    assert not_reviewed.status_code == 400
    assert get_daily_activity("2026-07-21", "chatgpt") is None

    object.__setattr__(settings, "daily_activity_ingest_token", "test-secret")
    try:
        payload["privacy_reviewed"] = True
        unauthorized = client.post("/api/daily-activities", json=payload)
        assert unauthorized.status_code == 401
        authorized = client.post(
            "/api/daily-activities",
            json=payload,
            headers={"Authorization": "Bearer test-secret"},
        )
        assert authorized.status_code == 200
    finally:
        object.__setattr__(settings, "daily_activity_ingest_token", "")

def test_notion_queue_pull_registers_and_retries_idempotently(monkeypatch):
    import json
    import pulda.connectors as connectors
    from pulda.config import settings

    envelope = {
        "kind": "pulda-daily-activity",
        "activity_date": "2026-07-22",
        "source_channel": "chatgpt",
        "external_key": "chatgpt:primary:2026-07-22",
        "source_coverage": "scheduled ChatGPT activity summary",
        "access_gaps": "account-wide transcript access unavailable",
        "privacy_reviewed": True,
        "items": [{
            "item_type": "work_result",
            "project": "PRJ-PULDA-OS",
            "summary": "Notion queue adapter test completed",
            "source_ref": "CR-0015",
            "review_state": "register",
        }],
    }

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [{
                    "type": "code",
                    "code": {"rich_text": [{"plain_text": json.dumps(envelope)}]},
                }],
                "has_more": False,
                "next_cursor": None,
            }

    monkeypatch.setattr(connectors, "_notion_request", lambda *args, **kwargs: FakeResponse())
    object.__setattr__(settings, "notion_daily_activity_queue_page_id", "queue-page")
    try:
        first = connectors.pull_notion_daily_activities()
        repeated = connectors.pull_notion_daily_activities()
    finally:
        object.__setattr__(settings, "notion_daily_activity_queue_page_id", "")

    assert first["ok"] is True
    assert first["processed"][0]["created"] is True
    assert first["processed"][0]["added_count"] == 1
    assert repeated["processed"][0]["created"] is False
    assert repeated["processed"][0]["added_count"] == 0
    assert repeated["processed"][0]["event_id"] == first["processed"][0]["event_id"]

def test_postgres_schema_and_sql_compatibility_adapter():
    from pulda.db import _postgres_schema, _postgres_sql, database_backend

    schema = _postgres_schema()
    assert "BIGSERIAL PRIMARY KEY" in schema
    assert "AUTOINCREMENT" not in schema
    assert "event_id BIGINT NOT NULL REFERENCES events(id)" in schema
    assert database_backend() == "sqlite"

    select_sql = _postgres_sql("SELECT * FROM events WHERE id=? AND status=?")
    assert select_sql == "SELECT * FROM events WHERE id=%s AND status=%s"

    ignore_sql = _postgres_sql(
        "INSERT OR IGNORE INTO daily_activity_items(batch_id,item_key) VALUES(?,?)"
    )
    assert ignore_sql == (
        "INSERT INTO daily_activity_items(batch_id,item_key) VALUES(%s,%s) "
        "ON CONFLICT DO NOTHING"
    )

def test_first_contextual_knowledge_case_is_idempotent_and_retrievable():
    item = capture_knowledge_source(
        canonical_url="https://www.cio.com/article/4196592/example",
        title="모두의 AI 지원사업",
        publisher="CIO Korea",
        published_at="2026-07-14",
        summary="정부가 범용 AI 챗봇과 공공 AI 에이전트를 지원한다.",
        relevance_note="Pulda OS의 소버린 AI 및 멀티모델 전환 대비 근거",
        tags=["소버린 AI", "공공 AI", "멀티모델"],
        related_contexts=["PRJ-PULDA-OS", "AI provider portability"],
        project="PRJ-PULDA-OS",
        metadata={"capture_case": "KNOW-0001"},
    )
    duplicate = capture_knowledge_source(
        canonical_url="https://www.cio.com/article/4196592/example",
        title="중복 제목은 적용되지 않음",
        summary="중복",
        relevance_note="중복",
    )
    assert duplicate["id"] == item["id"]
    assert duplicate["event_id"] == item["event_id"]
    assert item["archival_status"] == "reference_only"
    assert item["storage_format"] == "url-reference"
    assert item["metadata"]["capture_case"] == "KNOW-0001"

    relevant = find_relevant_knowledge("소버린 AI", project="PRJ-PULDA-OS")
    assert [row["id"] for row in relevant] == [item["id"]]
    assert "멀티모델" in relevant[0]["tags"]

def test_contextual_knowledge_case_is_executable_through_api():
    from fastapi.testclient import TestClient
    from pulda.app import app

    client = TestClient(app)
    payload = {
        "canonical_url": "https://www.cio.com/article/4196592/api-example",
        "title": "AI도 한글처럼",
        "publisher": "CIO Korea",
        "published_at": "2026-07-14",
        "summary": "전 국민 무료 AI 챗봇과 공공 AI 에이전트 사업",
        "relevance_note": "Pulda OS 모델 독립성과 실행 통제 설계에 관련",
        "tags": ["국산 AI", "AI 에이전트"],
        "related_contexts": ["PRJ-PULDA-OS"],
        "project": "PRJ-PULDA-OS",
    }
    captured = client.post("/api/knowledge-sources", json=payload)
    assert captured.status_code == 200
    source = captured.json()
    assert get_event(source["event_id"])["source"] == "knowledge:web"

    result = client.get(
        "/api/knowledge-sources/relevant",
        params={"query": "AI 에이전트", "project": "PRJ-PULDA-OS"},
    )
    assert result.status_code == 200
    assert any(row["id"] == source["id"] for row in result.json())

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

def test_context_workspace_labels_future_date_as_upcoming_not_past():
    # User-reported bug: picking a date after today showed "과거 기록"
    # (past record). Only a date strictly before today is a past record;
    # a date after today is an upcoming plan.
    today = today_kst().isoformat()
    future_day = (today_kst() + timedelta(days=3)).isoformat()
    past_day = (today_kst() - timedelta(days=3)).isoformat()

    today_ws = context_workspace("today", selected_date=today)
    assert today_ws["is_today"] is True
    assert today_ws["is_past"] is False
    assert today_ws["is_future"] is False

    future_ws = context_workspace("today", selected_date=future_day)
    assert future_ws["is_today"] is False
    assert future_ws["is_past"] is False
    assert future_ws["is_future"] is True

    past_ws = context_workspace("today", selected_date=past_day)
    assert past_ws["is_today"] is False
    assert past_ws["is_past"] is True
    assert past_ws["is_future"] is False

def test_status_change_is_recorded_and_appears_in_feed():
    # User request: status changes must be visible in the Event feed even
    # after the event leaves the "실행 후보" candidate list, not just a
    # silent column update.
    event_id = create_event("상태 변경 이력 테스트 이벤트")
    update_status(event_id, "doing")
    update_status(event_id, "done")

    workspace = context_workspace("today", selected_date=today_kst().isoformat())
    history_entries = [e for e in workspace["recent"] if e.get("kind") == "status_change" and e["event_id"] == event_id]
    assert len(history_entries) == 2
    transitions = {(e["from_status"], e["to_status"]) for e in history_entries}
    assert ("inbox", "doing") in transitions
    assert ("doing", "done") in transitions
    # No-op status update (same value) must not create a spurious entry.
    update_status(event_id, "done")
    workspace2 = context_workspace("today", selected_date=today_kst().isoformat())
    assert len([e for e in workspace2["recent"] if e.get("kind") == "status_change" and e["event_id"] == event_id]) == 2

def test_soft_delete_hides_event_but_keeps_history():
    # User request 2026-07-13: a normal delete must stay in the record
    # (soft-delete) and log a visible history entry, not vanish silently.
    event_id = create_event("숨김 삭제 테스트 이벤트")
    soft_delete_event(event_id)
    all_ids = [e["id"] for e in context_events("today", limit=1000)]
    assert event_id not in all_ids
    # The event row itself still exists (not purged) and is flagged deleted.
    event = get_event(event_id)
    assert event is not None
    assert event["deleted_at"] is not None
    workspace = context_workspace("today", selected_date=today_kst().isoformat())
    deletions = [e for e in workspace["recent"] if e.get("kind") == "status_change" and e["event_id"] == event_id and e["to_status"] == "deleted"]
    assert len(deletions) == 1

def test_hard_delete_purges_event_and_history():
    # Reserved for accidental duplicates (e.g. double-tapped submit) where
    # a permanent record would just be noise.
    event_id = create_event("완전 삭제 테스트 이벤트")
    update_status(event_id, "doing")
    delete_event(event_id)
    assert get_event(event_id) is None
    workspace = context_workspace("today", selected_date=today_kst().isoformat())
    assert not any(e.get("event_id") == event_id for e in workspace["recent"] if e.get("kind") == "status_change")

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

def test_home_has_no_tab_bar_single_context():
    # CR-0012/IA-0001 (superseding CR-0011): Home is a single Activity Feed —
    # there is no per-tab context to switch between. context_workspace's
    # "today" ctx must keep working as the sole Home view.
    text = f"프로젝트탭테스트 {datetime.now().isoformat()}"
    create_event(text, source="manual", project="탭리버트테스트")
    ws = context_workspace("today", today_kst().isoformat())
    assert any(text in e["text"] for e in ws["events"])

def test_projects_nav_lists_and_scopes_by_project():
    project_name = f"탭리버트테스트-{datetime.now().timestamp()}"
    create_event("프로젝트 전용 이벤트", source="manual", project=project_name)
    assert project_name in distinct_projects()
    scoped = context_events(f"project:{project_name}", limit=10)
    assert scoped and all(e["project"] == project_name for e in scoped)
