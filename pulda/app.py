import calendar
import uuid
from pathlib import Path
from datetime import date
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from .timeutil import today_kst
from .config import settings
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from .db import init_db
from .service import (
    create_event, list_events, update_status, today_plan, build_review, latest_review, health,
    get_event, update_event, defer_event, attention_items, delete_event, soft_delete_event,
    life_balance, decision_support, operations_summary, save_reflection,
    distinct_projects, context_workspace, context_events, calendar_activity, review_for_date,
    add_attachment, get_attachment, group_events_by_date,
    interpret_event, correct_interpretation, record_outcome, propose_follow_up,
    capture_knowledge_source, get_knowledge_source, find_relevant_knowledge,
    capture_daily_activity, get_daily_activity,
    bulk_update_status, list_workspace_tabs, add_workspace_tab, remove_workspace_tab,
    WORKSPACE_VIEWS, create_recurrence_series, recurrence_dates, set_occurrence_status,
)
from .connectors import (
    sync_notion, sync_github, check_notion, check_github,
    pull_notion_daily_activities,
)
from .scheduler import start_scheduler
from .config import settings

app = FastAPI(title="Pulda Runtime MVP", version="0.1.0")
templates = Jinja2Templates(directory="pulda/templates")

STATUS_LABELS = {
    "recorded": "기록됨", "doing": "진행중",
    "done": "완료", "deferred": "보류", "dropped": "중단", "deleted": "삭제됨",
    # Legacy history values remain readable after CR-0017's additive
    # migration; they are no longer offered as current status choices.
    "inbox": "기록됨", "planned": "기록됨",
}

class EventIn(BaseModel):
    text: str
    source: str = "api"
    occurred_on: str | None = None

class BulkStatusIn(BaseModel):
    event_ids: list[int]
    status: str

class RecurrenceIn(BaseModel):
    frequency: str
    starts_on: str
    interval_value: int = 1
    ends_on: str | None = None
    timezone: str = "Asia/Seoul"

class OccurrenceStatusIn(BaseModel):
    occurrence_date: str
    status: str
    note: str | None = None

class EventPatch(BaseModel):
    status: str | None = None
    role: str | None = None
    area: str | None = None
    kind: str | None = None
    urgency: int | None = None
    importance: int | None = None
    due_date: str | None = None
    scheduled_at: str | None = None
    project: str | None = None
    goal: str | None = None
    financial_impact: str | None = None
    family_impact: str | None = None
    blocked_by: str | None = None
    defer_reason: str | None = None
    next_review_at: str | None = None
    notion_page_id: str | None = None

class DeferIn(BaseModel):
    reason: str
    next_review_at: str | None = None

class InterpretationIn(BaseModel):
    model: str = "rule-based-v0"
    prompt_version: str = "living-loop-v0.1"
    dna_version: str = "notion-2026-07-15"
    confidence: float = 0.5

class CorrectionIn(BaseModel):
    field_name: str
    new_value: str
    rationale: str
    scope: str = "one_time"
    reusable_match_text: str | None = None

class OutcomeIn(BaseModel):
    result_text: str
    status: str = "recorded"

class FollowUpIn(BaseModel):
    outcome_id: int
    text: str

class KnowledgeSourceIn(BaseModel):
    canonical_url: str
    title: str
    summary: str
    relevance_note: str
    publisher: str | None = None
    published_at: str | None = None
    source_type: str = "web"
    storage_uri: str | None = None
    storage_format: str = "url-reference"
    archival_status: str = "reference_only"
    tags: list[str] = Field(default_factory=list)
    related_contexts: list[str] = Field(default_factory=list)
    content_hash: str | None = None
    metadata: dict = Field(default_factory=dict)
    project: str | None = None

class DailyActivityItemIn(BaseModel):
    item_key: str | None = None
    item_type: str
    project: str | None = None
    summary: str
    source_ref: str | None = None
    review_state: str = "register"

class DailyActivityIn(BaseModel):
    activity_date: str
    source_channel: str = "chatgpt"
    external_key: str
    source_coverage: str = ""
    access_gaps: str = ""
    privacy_reviewed: bool = False
    items: list[DailyActivityItemIn] = Field(default_factory=list)

def _require_daily_activity_token(request: Request) -> None:
    expected = settings.daily_activity_ingest_token
    if expected and request.headers.get("authorization") != f"Bearer {expected}":
        raise HTTPException(401, "invalid daily activity ingest token")

@app.on_event("startup")
def startup():
    init_db()
    start_scheduler()

def _month_grid(year: int, month: int, activity: dict[str, int], selected: str) -> list[list[dict | None]]:
    """Weeks x days grid (Sun-first, per user preference — 2026-07-13) for
    the mini calendar, each day carrying its activity count so density can
    render GitHub-contribution-style."""
    cal = calendar.Calendar(firstweekday=6)  # 6 = Sunday in the stdlib's Mon=0..Sun=6 scheme
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(None)
            else:
                iso = date(year, month, day).isoformat()
                row.append({"day": day, "iso": iso, "count": activity.get(iso, 0), "selected": iso == selected})
        weeks.append(row)
    return weeks

def _filter_home_events(events: list[dict], status: str | None, query: str | None) -> list[dict]:
    """Filter the selected day's Event rows without changing the date context."""
    normalized_query = (query or "").strip().casefold()
    return [
        event for event in events
        if event.get("kind") == "event"
        and (not status or status == "all" or event.get("status") == status)
        and (not normalized_query or normalized_query in event.get("text", "").casefold())
    ]


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    cal_date: str | None = None,
    status: str | None = None,
    q: str | None = None,
    group: str = "none",
    view: str = "home",
):
    """Home: the single Activity Feed (IA-0001/CR-0012, decided 2026-07-13,
    superseding the CR-0011 tab bar) — no central Event/Task/Goal/Project
    tabs to switch between. The only remaining context axis is the date
    picked from the sidebar calendar."""
    today_iso = today_kst().isoformat()
    # A date is "pinned" only when the user explicitly picked one via the
    # calendar — an unpinned view always tracks the live "today" and is
    # therefore eligible for automatic midnight rollover (Review v3 #2).
    pinned = cal_date is not None
    selected_date = cal_date or today_iso
    try:
        year, month = int(selected_date[:4]), int(selected_date[5:7])
    except ValueError:
        year, month = today_kst().year, today_kst().month
        selected_date = today_iso
        pinned = False
    if view not in WORKSPACE_VIEWS:
        view = "home"
    workspace = context_workspace("today", selected_date)
    review = review_for_date(selected_date)
    try:
        notion_status = check_notion()
    except Exception as e:
        notion_status = {"ok": False, "error": str(e)}
    display_events = _filter_home_events(workspace["recent"], status, q)
    change_history = [entry for entry in workspace["recent"] if entry.get("kind") == "status_change"]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "today": today_iso,
        "page": "home",
        "calendar_weeks": _month_grid(year, month, calendar_activity(year, month), selected_date),
        "calendar_label": f"{year}.{month:02d}",
        "selected_date": selected_date,
        "is_today": workspace["is_today"],
        "is_past": workspace["is_past"],
        "is_future": workspace["is_future"],
        "pinned": pinned,
        "events": workspace["events"],
        "events_grouped": workspace["events_grouped"],
        "display_events": display_events,
        "change_history": change_history,
        "event_filter": {"status": status or "all", "q": q or "", "group": group},
        "active_view": view,
        "workspace_tabs": list_workspace_tabs(),
        "workspace_view_options": [
            {"key": key, "label": label, "icon": icon}
            for key, (label, icon) in WORKSPACE_VIEWS.items()
            if key != "home" and key not in {tab["view_key"] for tab in list_workspace_tabs()}
        ],
        "plan": workspace["plan"],
        "recent_events": workspace["recent"],
        "review": review,
        "attention": workspace["attention"],
        "ops": workspace["ops"],
        "balance": life_balance(),
        "insights": decision_support(),
        "notion_status": notion_status,
        "status_labels": STATUS_LABELS,
        "status_options": ["recorded", "doing", "done", "deferred", "dropped"],
    })

@app.get("/projects", response_class=HTMLResponse)
def projects_index(request: Request):
    """Projects: its own nav destination (IA-0001), not a Home tab. Lists
    every project name currently in use, derived from Events the same way
    it always has been — just surfaced here instead of as a workspace tab."""
    projects = [{"name": name, "count": len(context_events(f"project:{name}", limit=1000))} for name in distinct_projects()]
    try:
        notion_status = check_notion()
    except Exception as e:
        notion_status = {"ok": False, "error": str(e)}
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "page": "projects",
        "projects": projects,
        "notion_status": notion_status,
    })

@app.get("/projects/{name}", response_class=HTMLResponse)
def project_detail(request: Request, name: str):
    events = context_events(f"project:{name}", limit=500)
    if not events:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다")
    try:
        notion_status = check_notion()
    except Exception as e:
        notion_status = {"ok": False, "error": str(e)}
    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "page": "projects",
        "project_name": name,
        "events_grouped": group_events_by_date(events),
        "status_labels": STATUS_LABELS,
        "notion_status": notion_status,
    })

ATTACHMENT_DIR = Path(settings.attachment_dir)

# Server-side allow-list — the UI's `accept` attribute only hints the file
# picker; it does not stop a direct POST from uploading anything. Audit
# finding #4: without this, an attacker could upload arbitrary file types
# (e.g. .html/.js) that browsers may render/execute on download.
ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".heic", ".webp", ".gif"}
ALLOWED_ATTACHMENT_MIME_PREFIXES = ("image/", "application/pdf")

def _validate_upload(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(400, f"허용되지 않는 파일 형식입니다: {suffix or '(확장자 없음)'}")
    if file.content_type and not file.content_type.startswith(ALLOWED_ATTACHMENT_MIME_PREFIXES):
        raise HTTPException(400, f"허용되지 않는 파일 형식입니다: {file.content_type}")

def _save_upload(file: UploadFile) -> tuple[str, int]:
    """Stream an uploaded file to disk under a random name (never trust the
    client-supplied filename for the path) and return (stored_name, size).
    Enforces PULDA_MAX_ATTACHMENT_MB so one bad upload can't fill the disk."""
    ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix[:10]
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = ATTACHMENT_DIR / stored_name
    max_bytes = settings.max_attachment_mb * 1024 * 1024
    size = 0
    try:
        with open(dest, "wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(413, f"파일이 너무 큽니다 (최대 {settings.max_attachment_mb}MB)")
                out.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    return stored_name, size

@app.post("/capture")
def capture(text: str = Form(...), occurred_on: str | None = Form(None), file: UploadFile | None = File(None)):
    # UX-0001: no mandatory category, project, goal, tag, or priority on
    # capture — role/area are inferred by the classifier only, never forced
    # by which tab the user happened to be in (that "context-first" tagging
    # went away with the CR-0011 tab bar it depended on).
    if not text.strip():
        raise HTTPException(400, "text required")
    event_date = occurred_on or today_kst().isoformat()
    try:
        date.fromisoformat(event_date)
    except ValueError:
        raise HTTPException(400, "occurred_on must be YYYY-MM-DD")
    event_id = create_event(text.strip(), source="manual_ui", occurred_on=event_date)
    if file is not None and file.filename:
        # Event and attachment aren't in a single DB transaction (attachment
        # writes hit the filesystem too), so on any upload failure the Event
        # is explicitly rolled back here rather than left as an orphan
        # empty capture (CR-0007 audit finding #3).
        try:
            _validate_upload(file)
            stored_name, size = _save_upload(file)
            add_attachment(event_id, file.filename, stored_name, file.content_type, size)
        except HTTPException:
            delete_event(event_id)
            raise
    dest = "/" if event_date == today_kst().isoformat() else f"/?cal_date={event_date}"
    return RedirectResponse(dest, status_code=303)

@app.post("/events/bulk-status")
def bulk_status(event_ids: list[int] = Form(...), status: str = Form(...), redirect_date: str | None = Form(None)):
    try:
        bulk_update_status(event_ids, status)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    dest = "/" if not redirect_date or redirect_date == today_kst().isoformat() else f"/?cal_date={redirect_date}"
    return RedirectResponse(dest, status_code=303)

@app.post("/workspace-tabs")
def workspace_tab_add(view_key: str = Form(...)):
    try:
        add_workspace_tab(view_key)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return RedirectResponse(f"/?view={view_key}", status_code=303)

@app.post("/workspace-tabs/{view_key}/remove")
def workspace_tab_remove(view_key: str):
    try:
        remove_workspace_tab(view_key)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return RedirectResponse("/", status_code=303)

@app.get("/attachments/{attachment_id}")
def download_attachment(attachment_id: int):
    attachment = get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(404, "attachment not found")
    path = ATTACHMENT_DIR / attachment["stored_name"]
    if not path.exists():
        raise HTTPException(404, "file missing on disk")
    return FileResponse(
        path,
        media_type=attachment["mime_type"] or "application/octet-stream",
        filename=attachment["original_name"],
        # Audit finding #4: force download instead of inline rendering, and
        # tell browsers not to MIME-sniff — an uploaded file must never be
        # executed/rendered as HTML/script in the app's own origin.
        content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff"},
    )

@app.post("/status/{event_id}")
def status(event_id: int, status: str = Form(...), redirect_date: str | None = Form(None)):
    update_status(event_id, status)
    # Only pin the date if it isn't the live "today" — otherwise this would
    # incorrectly flip an unpinned Today view into a pinned one.
    if redirect_date and redirect_date != today_kst().isoformat():
        dest = f"/?cal_date={redirect_date}"
    else:
        dest = "/"
    return RedirectResponse(dest, status_code=303)

@app.post("/events/{event_id}/delete")
def delete_event_route(event_id: int, mode: str = Form("soft"), redirect_date: str | None = Form(None)):
    """User-facing delete (2026-07-13). `mode=soft` (default) hides the
    event but keeps it and its history — the normal case. `mode=hard`
    permanently purges it with no trace, reserved for genuine duplicate
    captures (e.g. a double-tapped submit) where a permanent record would
    just be noise."""
    if mode == "hard":
        delete_event(event_id)
    else:
        soft_delete_event(event_id)
    if redirect_date and redirect_date != today_kst().isoformat():
        dest = f"/?cal_date={redirect_date}"
    else:
        dest = "/"
    return RedirectResponse(dest, status_code=303)

@app.post("/review")
def review_action():
    build_review()
    return RedirectResponse("/", status_code=303)

@app.post("/reviews/reflection")
def reflection_action(text: str = Form(...)):
    try:
        save_reflection(text.strip())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse("/", status_code=303)

@app.post("/sync/notion")
def notion_action():
    result = sync_notion()
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return RedirectResponse("/", status_code=303)

@app.post("/sync/github")
def github_action():
    result = sync_github()
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return RedirectResponse("/", status_code=303)

@app.post("/api/events")
def api_create_event(item: EventIn):
    return {"id": create_event(item.text, item.source, occurred_on=item.occurred_on or today_kst().isoformat())}

@app.post("/api/events/bulk-status")
def api_bulk_status(item: BulkStatusIn):
    try:
        return bulk_update_status(item.event_ids, item.status)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/events/{event_id}/recurrence")
def api_create_recurrence(event_id: int, item: RecurrenceIn):
    try:
        return create_recurrence_series(event_id, **item.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.get("/api/recurrences/{series_id}/dates")
def api_recurrence_dates(series_id: int, window_start: str, window_end: str):
    try:
        return recurrence_dates(series_id, window_start, window_end)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/recurrences/{series_id}/occurrences")
def api_occurrence_status(series_id: int, item: OccurrenceStatusIn):
    try:
        return set_occurrence_status(series_id, item.occurrence_date, item.status, item.note)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/daily-activities")
def api_capture_daily_activity(item: DailyActivityIn, request: Request):
    _require_daily_activity_token(request)
    try:
        return capture_daily_activity(
            activity_date=item.activity_date,
            source_channel=item.source_channel,
            external_key=item.external_key,
            source_coverage=item.source_coverage,
            access_gaps=item.access_gaps,
            privacy_reviewed=item.privacy_reviewed,
            items=[entry.model_dump() for entry in item.items],
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/daily-activities/{activity_date}")
def api_get_daily_activity(activity_date: str, request: Request, source_channel: str = "chatgpt"):
    _require_daily_activity_token(request)
    result = get_daily_activity(activity_date, source_channel)
    if not result:
        raise HTTPException(404, "daily activity not found")
    return result

@app.get("/api/events")
def api_events(status: str | None = None):
    return list_events(status=status)

@app.get("/api/events/attention")
def api_events_attention():
    return attention_items()

@app.post("/api/knowledge-sources")
def api_capture_knowledge_source(item: KnowledgeSourceIn):
    try:
        return capture_knowledge_source(**item.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/knowledge-sources/relevant")
def api_relevant_knowledge(query: str, project: str | None = None, limit: int = 10):
    return find_relevant_knowledge(query, project=project, limit=min(max(limit, 1), 100))

@app.get("/api/knowledge-sources/{source_id}")
def api_get_knowledge_source(source_id: int):
    source = get_knowledge_source(source_id)
    if not source:
        raise HTTPException(404, "knowledge source not found")
    return source

@app.get("/api/events/{event_id}")
def api_get_event(event_id: int):
    event = get_event(event_id)
    if not event:
        raise HTTPException(404, "event not found")
    return event

@app.patch("/api/events/{event_id}")
def api_patch_event(event_id: int, patch: EventPatch):
    try:
        return update_event(event_id, **patch.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/events/{event_id}/defer")
def api_defer_event(event_id: int, body: DeferIn):
    try:
        return defer_event(event_id, body.reason, body.next_review_at)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/events/{event_id}/interpretations")
def api_interpret_event(event_id: int, body: InterpretationIn):
    try:
        return interpret_event(event_id, **body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/interpretations/{interpretation_id}/corrections")
def api_correct_interpretation(interpretation_id: int, body: CorrectionIn):
    try:
        return correct_interpretation(interpretation_id, **body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/events/{event_id}/outcomes")
def api_record_outcome(event_id: int, body: OutcomeIn):
    try:
        return record_outcome(event_id, body.result_text, body.status)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/events/{event_id}/follow-ups")
def api_propose_follow_up(event_id: int, body: FollowUpIn):
    try:
        return propose_follow_up(event_id, body.outcome_id, body.text)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/today")
def api_today():
    return today_plan()

@app.post("/api/review")
def api_review():
    return build_review()

@app.get("/reviews/daily")
def reviews_daily():
    review = latest_review()
    if not review:
        raise HTTPException(404, "no review yet")
    return review

@app.get("/api/health")
def api_health():
    return health()

@app.get("/integrations/notion/check")
def integrations_notion_check():
    result = check_notion()
    if not result["ok"]:
        raise HTTPException(400, result)
    return result

@app.post("/integrations/notion/daily-activities/pull")
def integrations_notion_daily_activities_pull(request: Request):
    _require_daily_activity_token(request)
    result = pull_notion_daily_activities()
    if not result["ok"]:
        raise HTTPException(400, result)
    return result

@app.get("/integrations/github/check")
def integrations_github_check():
    result = check_github()
    if not result["ok"]:
        raise HTTPException(400, result)
    return result

def main():
    import uvicorn
    uvicorn.run("pulda.app:app", host=settings.host, port=settings.port, reload=False)

if __name__ == "__main__":
    main()
