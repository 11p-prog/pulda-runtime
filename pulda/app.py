import calendar
from datetime import date
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .db import init_db
from .service import (
    create_event, list_events, update_status, today_plan, build_review, latest_review, health,
    get_event, update_event, defer_event, attention_items,
    life_balance, decision_support, operations_summary, save_reflection,
    CONTEXT_TABS, distinct_projects, context_workspace, calendar_activity, review_for_date,
)
from .connectors import sync_notion, sync_github, check_notion, check_github
from .scheduler import start_scheduler
from .config import settings

app = FastAPI(title="Pulda Runtime MVP", version="0.1.0")
templates = Jinja2Templates(directory="pulda/templates")

STATUS_LABELS = {
    "inbox": "수집됨", "planned": "계획됨", "doing": "진행중",
    "done": "완료", "deferred": "보류", "dropped": "중단",
}

class EventIn(BaseModel):
    text: str
    source: str = "api"

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

@app.on_event("startup")
def startup():
    init_db()
    start_scheduler()

def _month_grid(year: int, month: int, activity: dict[str, int], selected: str) -> list[list[dict | None]]:
    """Weeks x days grid (Mon-first) for the mini calendar, each day carrying
    its activity count so density can render GitHub-contribution-style."""
    cal = calendar.Calendar(firstweekday=0)
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

def _workspace_tabs():
    tabs = [CONTEXT_TABS[0]]  # 오늘
    for name in distinct_projects():
        tabs.append({"ctx": f"project:{name}", "label": f"Project: {name}", "icon": "folder_open"})
    tabs.extend(CONTEXT_TABS[1:])  # Church / Family / Knowledge
    return tabs

@app.get("/", response_class=HTMLResponse)
def index(request: Request, ctx: str = "today", cal_date: str | None = None):
    tabs = _workspace_tabs()
    if ctx not in {t["ctx"] for t in tabs}:
        ctx = "today"
    today_iso = date.today().isoformat()
    # A date is "pinned" only when the user explicitly picked one via the
    # calendar — an unpinned view always tracks the live "today" and is
    # therefore eligible for automatic midnight rollover (Review v3 #2).
    pinned = cal_date is not None
    selected_date = cal_date or today_iso
    try:
        year, month = int(selected_date[:4]), int(selected_date[5:7])
    except ValueError:
        year, month = date.today().year, date.today().month
        selected_date = today_iso
        pinned = False
    workspace = context_workspace(ctx, selected_date)
    review = review_for_date(selected_date)
    try:
        notion_status = check_notion()
    except Exception as e:
        notion_status = {"ok": False, "error": str(e)}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "today": today_iso,
        "ctx": ctx,
        "tabs": tabs,
        "calendar_weeks": _month_grid(year, month, calendar_activity(year, month), selected_date),
        "calendar_label": f"{year}.{month:02d}",
        "selected_date": selected_date,
        "is_today": workspace["is_today"],
        "pinned": pinned,
        "events": workspace["events"] if ctx != "knowledge" else list_events(limit=50),
        "plan": workspace["plan"],
        "recent_events": workspace["recent"],
        "review": review,
        "attention": workspace["attention"],
        "ops": workspace["ops"],
        "balance": life_balance(),
        "insights": decision_support(),
        "notion_status": notion_status,
        "status_labels": STATUS_LABELS,
        "status_options": ["inbox", "planned", "doing", "done", "deferred", "dropped"],
    })

@app.post("/capture")
def capture(text: str = Form(...), ctx: str = Form("today")):
    if not text.strip():
        raise HTTPException(400, "text required")
    # Context-first: an Event captured while inside a workspace tab is
    # tagged with that tab's context automatically (UX v2), unless it's the
    # generic "today" or "knowledge" (no auto-classification yet) tab.
    role_override = None
    extra = {}
    if ctx.startswith("project:"):
        extra["project"] = ctx.split(":", 1)[1]
    elif ctx.startswith("role:"):
        role_override = ctx.split(":", 1)[1]
    create_event(text.strip(), role_override=role_override, **extra)
    return RedirectResponse(f"/?ctx={ctx}", status_code=303)

@app.post("/status/{event_id}")
def status(event_id: int, status: str = Form(...), ctx: str = Form("today")):
    update_status(event_id, status)
    return RedirectResponse(f"/?ctx={ctx}", status_code=303)

@app.post("/review")
def review_action(ctx: str = Form("today")):
    build_review()
    return RedirectResponse(f"/?ctx={ctx}", status_code=303)

@app.post("/reviews/reflection")
def reflection_action(text: str = Form(...), ctx: str = Form("today")):
    try:
        save_reflection(text.strip())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(f"/?ctx={ctx}", status_code=303)

@app.post("/sync/notion")
def notion_action(ctx: str = Form("today")):
    result = sync_notion()
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return RedirectResponse(f"/?ctx={ctx}", status_code=303)

@app.post("/sync/github")
def github_action(ctx: str = Form("today")):
    result = sync_github()
    if not result["ok"]:
        raise HTTPException(400, result["error"])
    return RedirectResponse(f"/?ctx={ctx}", status_code=303)

@app.post("/api/events")
def api_create_event(item: EventIn):
    return {"id": create_event(item.text, item.source)}

@app.get("/api/events")
def api_events(status: str | None = None):
    return list_events(status=status)

@app.get("/api/events/attention")
def api_events_attention():
    return attention_items()

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
