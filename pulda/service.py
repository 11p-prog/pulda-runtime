from datetime import datetime, date
from .timeutil import now_kst, today_kst, date_label
from .db import connect
from .classifier import classify

def audit(action: str, target: str | None, status: str, detail: str = "") -> None:
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(action,target,status,detail,created_at) VALUES(?,?,?,?,?)",
            (action, target, status, detail, now),
        )

def create_event(text: str, source: str = "manual", role_override: str | None = None, **extra) -> int:
    c = classify(text)
    role = role_override or c.role
    now = now_kst().isoformat(timespec="seconds")
    extra_fields = {
        "project": None, "goal": None, "financial_impact": None,
        "family_impact": None, "blocked_by": None, "defer_reason": None,
        "next_review_at": None, "notion_page_id": None,
    }
    extra_fields.update({k: v for k, v in extra.items() if k in extra_fields})
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO events
            (text,source,role,area,kind,urgency,importance,status,scheduled_at,due_date,
             project,goal,financial_impact,family_impact,blocked_by,defer_reason,next_review_at,notion_page_id,
             created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (text,source,role,c.area,c.kind,c.urgency,c.importance,c.status,
             c.scheduled_at,c.due_date,
             extra_fields["project"], extra_fields["goal"], extra_fields["financial_impact"],
             extra_fields["family_impact"], extra_fields["blocked_by"], extra_fields["defer_reason"],
             extra_fields["next_review_at"], extra_fields["notion_page_id"],
             now,now),
        )
        event_id = cur.lastrowid
    audit("create_event", str(event_id), "success", text)
    return event_id

def get_event(event_id: int):
    with connect() as conn:
        row = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    return dict(row) if row else None

def delete_event(event_id: int) -> None:
    """Hard-delete an event and any attachments it owns. Used to roll back
    an Event created by /capture when the accompanying file upload fails,
    so a rejected attachment never leaves a silent empty Event behind
    (CR-0007 audit finding #3)."""
    with connect() as conn:
        conn.execute("DELETE FROM attachments WHERE event_id=?", (event_id,))
        conn.execute("DELETE FROM events WHERE id=?", (event_id,))
    audit("delete_event", str(event_id), "success", "")

PATCHABLE_FIELDS = {
    "status", "role", "area", "kind", "urgency", "importance", "due_date",
    "scheduled_at", "project", "goal", "financial_impact", "family_impact",
    "blocked_by", "defer_reason", "next_review_at", "notion_page_id",
}

def update_event(event_id: int, **fields) -> dict:
    if not get_event(event_id):
        raise ValueError("event not found")
    updates = {k: v for k, v in fields.items() if k in PATCHABLE_FIELDS and v is not None}
    if not updates:
        raise ValueError("no valid fields to update")
    if "status" in updates:
        allowed = {"inbox","planned","doing","done","deferred","dropped"}
        if updates["status"] not in allowed:
            raise ValueError("invalid status")
    now = now_kst().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k}=?" for k in updates) + ", updated_at=?"
    params = list(updates.values()) + [now, event_id]
    with connect() as conn:
        conn.execute(f"UPDATE events SET {set_clause} WHERE id=?", params)
    audit("update_event", str(event_id), "success", ",".join(updates.keys()))
    return get_event(event_id)

def defer_event(event_id: int, reason: str, next_review_at: str | None = None) -> dict:
    if not get_event(event_id):
        raise ValueError("event not found")
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            "UPDATE events SET status='deferred', defer_reason=?, next_review_at=?, updated_at=? WHERE id=?",
            (reason, next_review_at, now, event_id),
        )
    audit("defer_event", str(event_id), "success", reason)
    return get_event(event_id)

def list_events(status: str | None = None, limit: int = 100):
    q = "SELECT * FROM events"
    params = []
    if status:
        q += " WHERE status=?"
        params.append(status)
    q += " ORDER BY importance DESC, urgency DESC, created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return [dict(r) for r in conn.execute(q, params).fetchall()]

def update_status(event_id: int, status: str) -> None:
    allowed = {"inbox","planned","doing","done","deferred","dropped"}
    if status not in allowed:
        raise ValueError("invalid status")
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute("UPDATE events SET status=?, updated_at=? WHERE id=?", (status, now, event_id))
    audit("update_status", str(event_id), "success", status)

def attention_items() -> dict:
    """Events needing follow-up: overdue, deferred, or blocked — per
    MVP_SPEC.md's 'show blocked/overdue/deferred items' requirement."""
    today = today_kst().isoformat()
    with connect() as conn:
        overdue = conn.execute(
            """SELECT * FROM events WHERE status NOT IN ('done','dropped')
            AND due_date IS NOT NULL AND due_date < ?
            ORDER BY due_date ASC""",
            (today,),
        ).fetchall()
        deferred = conn.execute(
            "SELECT * FROM events WHERE status='deferred' ORDER BY next_review_at ASC, updated_at DESC"
        ).fetchall()
        blocked = conn.execute(
            "SELECT * FROM events WHERE blocked_by IS NOT NULL AND status NOT IN ('done','dropped') ORDER BY updated_at DESC"
        ).fetchall()
    return {
        "overdue": [dict(r) for r in overdue],
        "deferred": [dict(r) for r in deferred],
        "blocked": [dict(r) for r in blocked],
    }

def today_plan():
    today = today_kst().isoformat()
    with connect() as conn:
        rows = conn.execute(
            """SELECT * FROM events
            WHERE status NOT IN ('done','dropped')
              AND (due_date=? OR urgency>=4 OR importance>=4)
            ORDER BY importance DESC, urgency DESC, created_at ASC""",
            (today,),
        ).fetchall()
    return [dict(r) for r in rows]

def build_review() -> dict:
    today = today_kst().isoformat()
    with connect() as conn:
        done = conn.execute(
            "SELECT * FROM events WHERE status='done' AND substr(updated_at,1,10)=?", (today,)
        ).fetchall()
        open_rows = conn.execute(
            "SELECT * FROM events WHERE status NOT IN ('done','dropped') ORDER BY importance DESC, urgency DESC"
        ).fetchall()
    summary = (
        f"# {today} Daily Review\n\n"
        f"- 완료: {len(done)}건\n"
        f"- 미완료/진행: {len(open_rows)}건\n\n"
        "## 완료\n" + ("\n".join(f"- {r['text']}" for r in done) or "- 없음") +
        "\n\n## 다음 검토 대상\n" +
        ("\n".join(f"- [{r['status']}] {r['text']}" for r in open_rows[:10]) or "- 없음")
    )
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            """INSERT INTO reviews(review_date,summary,created_at) VALUES(?,?,?)
            ON CONFLICT(review_date) DO UPDATE SET summary=excluded.summary, created_at=excluded.created_at""",
            (today, summary, now),
        )
    audit("build_review", today, "success", f"done={len(done)}, open={len(open_rows)}")
    return {"review_date": today, "summary": summary}

def latest_review():
    with connect() as conn:
        row = conn.execute("SELECT * FROM reviews ORDER BY review_date DESC LIMIT 1").fetchone()
    return dict(row) if row else None

def review_for_date(review_date: str):
    """Look up the review for a specific date — used so the review panel
    reflects the selected workspace date, not always 'the latest review'
    (Review v3 #1/#6: date is a workspace context, not decoration)."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE review_date=?", (review_date,)).fetchone()
    return dict(row) if row else None

def save_reflection(text: str, review_date: str | None = None) -> dict:
    """Attach a one-line daily reflection to a review, as part of the review
    flow rather than a standalone always-on widget."""
    review_date = review_date or today_kst().isoformat()
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        existing = conn.execute("SELECT id FROM reviews WHERE review_date=?", (review_date,)).fetchone()
        if not existing:
            raise ValueError("no review for that date yet — generate the daily review first")
        conn.execute(
            "UPDATE reviews SET reflection=? WHERE review_date=?",
            (text, review_date),
        )
        row = conn.execute("SELECT * FROM reviews WHERE review_date=?", (review_date,)).fetchone()
    audit("save_reflection", review_date, "success", text[:80])
    return dict(row)

# role/area -> life-balance bucket. Best-effort mapping given the current
# domain model (role: 가족/회사/성당/개인, area includes 건강/학습/재무/...).
# Not a precise ontology — revisit if/when the domain model gains explicit
# Business/Family/Health/Learning fields.
def _balance_bucket(role: str, area: str) -> str:
    if role == "가족" or area == "관계":
        return "family"
    if area == "건강":
        return "health"
    if area == "학습" or role == "성당":
        return "learning"
    return "business"

BALANCE_LABELS = {
    "business": "업무",
    "family": "가족",
    "health": "건강",
    "learning": "성장/학습",
}

def life_balance() -> dict:
    """Share of currently active (non-done/dropped) events across life-
    balance buckets. Reflects where attention is currently going, not a
    judgment of what it should be.

    Per Review v3 #3 ("Remove Placeholder Widgets"): a bucket only appears
    once it has real data (count > 0) — a 0건/0% bucket is an invented
    metric, not a signal, so it's omitted rather than shown empty."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, area FROM events WHERE status NOT IN ('done','dropped')"
        ).fetchall()
    counts = {"business": 0, "family": 0, "health": 0, "learning": 0}
    for r in rows:
        counts[_balance_bucket(r["role"], r["area"])] += 1
    total = sum(counts.values())
    return {
        "total": total,
        "buckets": [
            {
                "key": key,
                "label": BALANCE_LABELS[key],
                "count": count,
                "pct": round(count / total * 100) if total else 0,
            }
            for key, count in counts.items()
            if count > 0
        ],
    }

def decision_support() -> list[dict]:
    """Rule-based decision-support signals derived from real event data (no
    LLM call — deterministic heuristics over what's actually in the system)."""
    today = today_kst().isoformat()
    insights: list[dict] = []
    with connect() as conn:
        overdue = conn.execute(
            "SELECT count(*) c FROM events WHERE status NOT IN ('done','dropped') AND due_date IS NOT NULL AND due_date < ?",
            (today,),
        ).fetchone()["c"]
        blocked = conn.execute(
            "SELECT text FROM events WHERE blocked_by IS NOT NULL AND status NOT IN ('done','dropped') ORDER BY updated_at DESC LIMIT 3"
        ).fetchall()
        cash = conn.execute(
            "SELECT count(*) c FROM events WHERE area='재무' AND status NOT IN ('done','dropped')"
        ).fetchone()["c"]
        stale_deferred = conn.execute(
            "SELECT count(*) c FROM events WHERE status='deferred' AND next_review_at IS NOT NULL AND next_review_at < ?",
            (today,),
        ).fetchone()["c"]

    if overdue:
        insights.append({"level": "warning", "text": f"기한이 지난 항목이 {overdue}건 있습니다."})
    for b in blocked:
        insights.append({"level": "info", "text": f"차단 상태: {b['text']}"})
    if cash:
        insights.append({"level": "warning", "text": f"재무 관련 미해결 항목이 {cash}건 있습니다. 현금흐름을 확인하세요."})
    if stale_deferred:
        insights.append({"level": "info", "text": f"재검토 시점이 지난 보류 항목이 {stale_deferred}건 있습니다."})
    if not insights:
        insights.append({"level": "ok", "text": "특별한 위험 신호가 없습니다. 지금 흐름을 유지하세요."})
    return insights

def operations_summary() -> dict:
    """The one-line operational status shown at the top of the app instead
    of a generic greeting."""
    today = today_kst().isoformat()
    focus_count = len(today_plan())
    with connect() as conn:
        waiting = conn.execute(
            "SELECT count(*) c FROM events WHERE status='inbox'"
        ).fetchone()["c"]
        blocked = conn.execute(
            "SELECT count(*) c FROM events WHERE blocked_by IS NOT NULL AND status NOT IN ('done','dropped')"
        ).fetchone()["c"]
        completed_today = conn.execute(
            "SELECT count(*) c FROM events WHERE status='done' AND substr(updated_at,1,10)=?", (today,)
        ).fetchone()["c"]
        family_priority = conn.execute(
            "SELECT count(*) c FROM events WHERE role='가족' AND status NOT IN ('done','dropped') AND (urgency>=4 OR importance>=4)"
        ).fetchone()["c"] > 0
        cash_caution = conn.execute(
            "SELECT count(*) c FROM events WHERE area='재무' AND status NOT IN ('done','dropped')"
        ).fetchone()["c"] > 0
    signals = []
    if family_priority:
        signals.append("가족 우선")
    if cash_caution:
        signals.append("현금흐름 주의")
    return {
        "focus_count": focus_count,
        "waiting_count": waiting,
        "blocked_count": blocked,
        "completed_today": completed_today,
        "signals": signals,
    }

# Presets offered in the "+" add-tab picker (CR-0011). Drafted from the
# role vocabulary the classifier already assigns events to
# (classifier.ROLE_KEYWORDS: 가족/회사/성당/개인) plus the Knowledge
# placeholder — these are suggestions, not a fixed set; the underlying
# workspace_tabs table is fully user-managed (add/remove any ctx).
TAB_PRESETS = [
    {"ctx": "role:성당", "label": "Church", "icon": "church"},
    {"ctx": "role:가족", "label": "Family", "icon": "diversity_3"},
    {"ctx": "role:회사", "label": "Work", "icon": "work"},
    {"ctx": "role:개인", "label": "Personal", "icon": "person"},
    {"ctx": "knowledge", "label": "Knowledge", "icon": "school"},
]

def list_workspace_tabs() -> list[dict]:
    """User-managed workspace tabs, in display order. '오늘' is always
    present (seeded non-removable, and the UI never offers a delete
    control for it) so the workspace always has a default landing tab."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT ctx, label, icon, removable, sort_order FROM workspace_tabs ORDER BY sort_order, id"
        ).fetchall()
    return [dict(r) for r in rows]

def add_workspace_tab(ctx: str, label: str, icon: str = "tab") -> dict:
    if not ctx or not label.strip():
        raise ValueError("ctx and label are required")
    with connect() as conn:
        existing = conn.execute("SELECT id FROM workspace_tabs WHERE ctx=?", (ctx,)).fetchone()
        if existing:
            raise ValueError("이미 존재하는 탭입니다")
        max_order = conn.execute("SELECT COALESCE(MAX(sort_order),0) m FROM workspace_tabs").fetchone()["m"]
        conn.execute(
            "INSERT INTO workspace_tabs(ctx,label,icon,removable,sort_order) VALUES(?,?,?,1,?)",
            (ctx, label.strip(), icon, max_order + 10),
        )
    audit("add_workspace_tab", ctx, "success", label)
    return {"ctx": ctx, "label": label.strip(), "icon": icon}

def remove_workspace_tab(ctx: str) -> None:
    if ctx == "today":
        raise ValueError("오늘 탭은 제거할 수 없습니다")
    with connect() as conn:
        row = conn.execute("SELECT removable FROM workspace_tabs WHERE ctx=?", (ctx,)).fetchone()
        if not row:
            raise ValueError("존재하지 않는 탭입니다")
        conn.execute("DELETE FROM workspace_tabs WHERE ctx=?", (ctx,))
    audit("remove_workspace_tab", ctx, "success", "")

def distinct_projects() -> list[str]:
    """Project names currently in use, used to build one workspace tab per
    active project (VS Code-style, per UX v2)."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT project FROM events WHERE project IS NOT NULL AND project<>'' ORDER BY project"
        ).fetchall()
    return [r["project"] for r in rows]

def _ctx_clause(ctx: str):
    """Translate a workspace-tab context id into a SQL WHERE fragment + param.
    ctx is 'today' | 'knowledge' | 'project:<name>' | 'role:<role>'."""
    if ctx.startswith("project:"):
        return "project=?", ctx.split(":", 1)[1]
    if ctx.startswith("role:"):
        return "role=?", ctx.split(":", 1)[1]
    return None, None

def add_attachment(event_id: int, original_name: str, stored_name: str, mime_type: str | None, size_bytes: int) -> dict:
    if not get_event(event_id):
        raise ValueError("event not found")
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO attachments(event_id, original_name, stored_name, mime_type, size_bytes, created_at)
            VALUES(?,?,?,?,?,?)""",
            (event_id, original_name, stored_name, mime_type, size_bytes, now),
        )
        attachment_id = cur.lastrowid
    audit("add_attachment", str(event_id), "success", original_name)
    return get_attachment(attachment_id)

def get_attachment(attachment_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM attachments WHERE id=?", (attachment_id,)).fetchone()
    return dict(row) if row else None

def list_attachments(event_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM attachments WHERE event_id=? ORDER BY created_at ASC", (event_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def _attach_files(events: list[dict]) -> list[dict]:
    """Populate each event dict with its `attachments` list in one query,
    so listing events never triggers N+1 lookups (personal-scale data, but
    still worth avoiding as attachments are shown in every list view)."""
    if not events:
        return events
    ids = [e["id"] for e in events]
    placeholders = ",".join("?" * len(ids))
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM attachments WHERE event_id IN ({placeholders}) ORDER BY created_at ASC", ids
        ).fetchall()
    by_event: dict[int, list[dict]] = {}
    for r in rows:
        by_event.setdefault(r["event_id"], []).append(dict(r))
    for e in events:
        e["attachments"] = by_event.get(e["id"], [])
    return events

def context_events(ctx: str, limit: int = 500):
    where, param = _ctx_clause(ctx)
    q = "SELECT * FROM events"
    params: list = []
    if where:
        q += f" WHERE {where}"
        params.append(param)
    q += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        events = [dict(r) for r in conn.execute(q, params).fetchall()]
    return _attach_files(events)

def context_workspace(ctx: str, selected_date: str | None = None) -> dict:
    """Everything the center 'workspace' panel needs for a given (domain,
    date) workspace: scoped operational stats, an execution/lookback list,
    attention items, and the mandatory Recent Events list.

    Per Review v3 #1/#6: the workspace has two independent context axes —
    domain (ctx) and date (selected_date). Picking a date is a real context
    switch, not calendar decoration: the center view must show *that day's*
    events/focus/logs/review, not just highlight a cell. Live-state sections
    (Waiting/Overdue/Blocked/Deferred) only make sense for 'now', so they're
    populated for today and left empty for a historical date — the
    historical view is a day's record, not a pretend live dashboard."""
    today = today_kst().isoformat()
    selected_date = selected_date or today
    is_today = selected_date == today
    if ctx == "knowledge":
        # Knowledge has no capture path yet (sidebar still says "준비중"),
        # but the date axis must behave the same as every other tab: picking
        # a date shows that date's (currently empty) record, not a
        # permanently blank stub regardless of which date is selected.
        return {
            "events": [], "events_grouped": [], "plan": [], "recent": [],
            "attention": {"overdue": [], "deferred": [], "blocked": []},
            "ops": {"focus_count": 0, "waiting_count": 0, "blocked_count": 0, "completed_today": 0},
            "is_today": is_today, "selected_date": selected_date,
        }
    all_events = context_events(ctx)
    day_events = [e for e in all_events if e["created_at"][:10] == selected_date]
    open_events = [e for e in all_events if e["status"] not in ("done", "dropped")]
    completed = [e for e in all_events if e["status"] == "done" and e["updated_at"][:10] == selected_date]

    # Per CR-0002/CR-0003: a historical date is a record of *that day*, not
    # a lens onto the whole context. "recent" is always day-scoped (an
    # empty day genuinely has nothing to show — falling back to unrelated
    # past events under a "최근 Event"/"오늘" label would misrepresent what
    # happened). The "전체 Event" table is date-scoped on a historical day
    # too; only the live Today view legitimately shows the whole context.
    recent = sorted(day_events, key=lambda e: e["created_at"], reverse=True)

    if is_today:
        plan = sorted(
            (e for e in open_events if e["due_date"] == today or e["urgency"] >= 4 or e["importance"] >= 4),
            key=lambda e: (-e["importance"], -e["urgency"], e["created_at"]),
        )
        overdue = sorted(
            (e for e in open_events if e["due_date"] and e["due_date"] < today),
            key=lambda e: e["due_date"],
        )
        deferred = sorted(
            (e for e in all_events if e["status"] == "deferred"),
            key=lambda e: (e["next_review_at"] or "9999-99-99", e["updated_at"]),
        )
        blocked = [e for e in open_events if e["blocked_by"]]
        waiting = [e for e in all_events if e["status"] == "inbox"]
        events = all_events
    else:
        # Historical day: no live-state sections — show what actually
        # happened that day instead of pretending it's a live dashboard.
        plan = sorted(day_events, key=lambda e: (-e["importance"], -e["urgency"], e["created_at"]))
        overdue, deferred, blocked = [], [], []
        waiting = [e for e in day_events if e["status"] == "inbox"]
        events = day_events

    return {
        "events": events,
        "events_grouped": group_events_by_date(events),
        "plan": plan,
        "recent": recent,
        "attention": {"overdue": overdue, "deferred": deferred, "blocked": blocked},
        "ops": {
            "focus_count": len(plan),
            "waiting_count": len(waiting),
            "blocked_count": len(blocked),
            "completed_today": len(completed),
        },
        "is_today": is_today,
        "selected_date": selected_date,
    }

def group_events_by_date(events: list[dict]) -> list[dict]:
    """Bucket an events list (already sorted, any order) into day groups for
    the log-style '전체 Event' view (CR-0009): a flat table with no time
    axis reads as "notes piling up"; grouping by day with a relative label
    (오늘/어제/N일 전) restores the sense that activity is being recorded.
    Groups preserve the input's per-event order and are emitted in the
    order their first event appears, so a DESC-sorted input yields
    newest-day-first groups."""
    today = today_kst()
    groups: dict[str, dict] = {}
    order: list[str] = []
    for e in events:
        d = e["created_at"][:10]
        if d not in groups:
            groups[d] = {"date": d, "label": date_label(d, today), "events": []}
            order.append(d)
        groups[d]["events"].append(e)
    return [groups[d] for d in order]


def calendar_activity(year: int, month: int) -> dict[str, int]:
    """Per-day capture counts for the given month — feeds the mini
    calendar's GitHub-contribution-style density indicators. The calendar is
    a fast date selector, not the primary view (per UX v2)."""
    prefix = f"{year:04d}-{month:02d}"
    with connect() as conn:
        rows = conn.execute(
            "SELECT substr(created_at,1,10) d, count(*) c FROM events WHERE substr(created_at,1,7)=? GROUP BY d",
            (prefix,),
        ).fetchall()
    return {r["d"]: r["c"] for r in rows}

def health():
    with connect() as conn:
        event_count = conn.execute("SELECT count(*) c FROM events").fetchone()["c"]
        failures = conn.execute(
            "SELECT * FROM audit_log WHERE status='failed' ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
    return {"status": "ok" if not failures else "degraded", "events": event_count,
            "recent_failures": [dict(r) for r in failures]}
