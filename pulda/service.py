from datetime import datetime, date
from .db import connect
from .classifier import classify

def audit(action: str, target: str | None, status: str, detail: str = "") -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(action,target,status,detail,created_at) VALUES(?,?,?,?,?)",
            (action, target, status, detail, now),
        )

def create_event(text: str, source: str = "manual", role_override: str | None = None, **extra) -> int:
    c = classify(text)
    role = role_override or c.role
    now = datetime.now().isoformat(timespec="seconds")
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
    now = datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k}=?" for k in updates) + ", updated_at=?"
    params = list(updates.values()) + [now, event_id]
    with connect() as conn:
        conn.execute(f"UPDATE events SET {set_clause} WHERE id=?", params)
    audit("update_event", str(event_id), "success", ",".join(updates.keys()))
    return get_event(event_id)

def defer_event(event_id: int, reason: str, next_review_at: str | None = None) -> dict:
    if not get_event(event_id):
        raise ValueError("event not found")
    now = datetime.now().isoformat(timespec="seconds")
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
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute("UPDATE events SET status=?, updated_at=? WHERE id=?", (status, now, event_id))
    audit("update_status", str(event_id), "success", status)

def attention_items() -> dict:
    """Events needing follow-up: overdue, deferred, or blocked — per
    MVP_SPEC.md's 'show blocked/overdue/deferred items' requirement."""
    today = date.today().isoformat()
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
    today = date.today().isoformat()
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
    today = date.today().isoformat()
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
    now = datetime.now().isoformat(timespec="seconds")
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
    review_date = review_date or date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")
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
    today = date.today().isoformat()
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
    today = date.today().isoformat()
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

CONTEXT_TABS = [
    {"ctx": "today", "label": "오늘", "icon": "target"},
    {"ctx": "role:성당", "label": "Church", "icon": "church"},
    {"ctx": "role:가족", "label": "Family", "icon": "diversity_3"},
    {"ctx": "knowledge", "label": "Knowledge", "icon": "school"},
]

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
        return [dict(r) for r in conn.execute(q, params).fetchall()]

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
    today = date.today().isoformat()
    selected_date = selected_date or today
    is_today = selected_date == today
    if ctx == "knowledge":
        return {
            "events": [], "plan": [], "recent": [],
            "attention": {"overdue": [], "deferred": [], "blocked": []},
            "ops": {"focus_count": 0, "waiting_count": 0, "blocked_count": 0, "completed_today": 0},
            "is_today": is_today, "selected_date": selected_date,
        }
    events = context_events(ctx)
    day_events = [e for e in events if e["created_at"][:10] == selected_date]
    open_events = [e for e in events if e["status"] not in ("done", "dropped")]
    completed = [e for e in events if e["status"] == "done" and e["updated_at"][:10] == selected_date]

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
            (e for e in events if e["status"] == "deferred"),
            key=lambda e: (e["next_review_at"] or "9999-99-99", e["updated_at"]),
        )
        blocked = [e for e in open_events if e["blocked_by"]]
        waiting = [e for e in events if e["status"] == "inbox"]
        recent = day_events if day_events else sorted(events, key=lambda e: e["created_at"], reverse=True)[:15]
    else:
        # Historical day: no live-state sections — show what actually
        # happened that day instead of pretending it's a live dashboard.
        plan = sorted(day_events, key=lambda e: (-e["importance"], -e["urgency"], e["created_at"]))
        overdue, deferred, blocked = [], [], []
        waiting = [e for e in day_events if e["status"] == "inbox"]
        recent = sorted(day_events, key=lambda e: e["created_at"], reverse=True)

    return {
        "events": events,
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
