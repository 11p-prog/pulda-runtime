# Changelog

## Unreleased

- 2026-07-16 — Exposed the first backend Living Loop through API endpoints for
  versioned interpretation, human correction, outcome recording, and follow-up
  proposals. Added an API-boundary regression test proving that a reusable
  correction changes the next comparable interpretation, and established
  `docs/HELP.md` as the living user guide.

- 2026-07-14 — Phase 0 governance reset integrated without adding duplicate
  operating/privacy documents:
  - added root `AGENTS.md` and versioned `PROJECT_INSTRUCTIONS.md`;
  - expanded the existing governance operating model with source authority,
    new-chat bootstrap, conflict resolution, anti-fragmentation, and living
    synchronization gates;
  - added CR-0013 to Git and corrected CR-0005 from Deferred to Blocked;
  - added explicit data export/import/restore and Builder handoff requirements;
  - clarified that the current Runtime is executable but the living AI loop is
    not yet implemented or user-verified.

- 2026-07-13 — Event delete (user request): "삭제" control added to every
  event list (오늘 실행 후보 / 최근 Event / 전체 Event), with a click-to-confirm
  panel offering two modes:
  - 숨김 삭제 (soft, default) — hides the event from all lists but keeps the
    row and logs a `deleted` transition into the same status-history feed,
    so it's still auditable later.
  - 완전 삭제 (hard) — purges the event, its attachments, and its history
    rows outright; reserved for genuine duplicate captures (e.g. a
    double-tapped submit) where no record is worth keeping.
  - `events.deleted_at` column added (migration-on-startup); every event
    query that feeds a visible list now filters `deleted_at IS NULL`.
- 2026-07-12/13 — Status-change history in the Event feed (user request):
  changing an event's status from any list (not just the 오늘 실행 후보
  card) now records a `from → to` entry in a new `event_history` table,
  merged into both "최근 Event" and "전체 Event" as a lightweight read-only
  row so the transition stays visible even after the event leaves the
  candidate list. Status-change forms carry a hidden `redirect_date` so
  changing status from a historical/future day returns to that day instead
  of always bouncing to today.
- 2026-07-12 — Fixed a calendar-header bug: future dates were mislabeled
  "과거 기록" (past record) instead of showing no suffix (today) or "다가올
  계획" (upcoming plan).

- Extended CR-0000 into a full CR/ADR/RFC document system per user
  direction: Git (`docs/cr/`, `docs/adr/`, `docs/rfc/`) is the source of
  truth for all three document types (one cumulative file per item; never
  forked); Notion is an operations dashboard only (mirrors CR Number/
  Title/Priority/Status/Owner/Reviewer/Created/Updated/links, never CR
  content). Unified status lifecycle: Draft → Review → Approved → In
  Progress → Implemented → User Verified → Closed (+ Blocked/Rejected/
  Deferred) — Implemented is explicitly not Closed; only the user can move
  a CR to User Verified/Closed.
  - Split the single CR status doc into `docs/cr/CR-0000.md`..`CR-0006.md`
    (unified template) plus `docs/cr/STATUS.md` as the canonical index.
  - Added `docs/adr/ADR-0001..0003.md` recording decisions already made:
    Workspace model over Dashboard, Event First, Calendar is Navigation.
  - Added `docs/rfc/RFC-0001..0003.md` for open (not-yet-decided) topics:
    AI memory structure, personal-data sensitivity layers, import engine
    design — companions to the deferred CR-0005 and existing
    `docs/IMPORT_PIPELINE.md`.
  - Set CR-0001/0002/0003/0004/0006 status to Implemented (awaiting User
    Verified); CR-0005 remains Deferred.

- Adopted CR-0000 (Pulda AI Collaboration Protocol): the user's ChatGPT
  "Chief Architect" issues Change Requests, this agent implements as
  "Runtime Engineer" and updates docs afterward. Copied the protocol into
  `docs/cr/CR-0000_AI_Collaboration_Protocol.md` (GitHub is the canonical
  doc location per the protocol) and added `docs/cr/CR_STATUS.md` tracking
  CR-0001..CR-0006 — CR-0001/0002/0003/0004/0006 are done (matches work
  already shipped this session), CR-0005 (Historical Import Framework) is
  deferred to Phase 2 per prior explicit user direction.

- Review v3: date + domain are now two independent workspace context axes,
  and placeholder metrics were removed, per user product review:
  - Selecting a calendar date is a real context switch, not decoration —
    `context_workspace(ctx, selected_date)` now scopes the plan, ops stats,
    Recent Events, and full event table to that date. Live-only sections
    (Waiting/Overdue/Deferred) only render for the live Today view; a
    historical date shows what actually happened that day instead (via a
    day-scoped "주요 항목"/record list and `review_for_date`).
  - "Today" now follows real local time without a reload: the header embeds
    the server's today-date and whether the view is pinned to a manually
    chosen date; unpinned views poll the client clock and auto-reload at
    local midnight, while a pinned historical date is left alone until the
    user clicks the new "Today로 돌아가기" button.
  - Removed the placeholder Health metric: `life_balance()` now omits any
    bucket with zero real data instead of showing an invented 0건/0%.
  - Added `docs/PRIVACY_ARCHITECTURE.md` covering the 8 privacy principles
    from the review, the current external-data-flow surface (Notion/GitHub
    sync), required guardrails for future AI/import features, and local-AI
    preparation notes.
  - Historical Google Docs import (review item #4) was explicitly deferred
    at the user's direction — not built this round.

- UX v2: introduced a VS Code/Replit-style workspace model on top of the v1
  interaction-hierarchy change, per user feedback that the app still felt
  dashboard-like rather than a workspace:
  - Center content is now organized into workspace tabs (Today, one tab per
    active `project`, Church/`role=성당`, Family/`role=가족`, Knowledge
    placeholder) — `pulda.service.context_workspace()` /
    `distinct_projects()` scope stats, the execution-candidate plan,
    attention items, and the event table to the active tab via a new `ctx`
    query/form param threaded through every route.
  - Context-first capture: the bottom capture bar submits the active `ctx`;
    `create_event()` gained `role_override` so captures made inside a
    Church/Family tab are tagged with that role automatically, and captures
    inside a Project tab get that `project` set automatically — no manual
    categorization needed. A small hint above the capture bar shows where
    the next capture will be saved.
  - Added a mandatory "최근 Event" (Recent Events) panel — chronological
    (not priority-sorted) list with capture time, status, and context;
    click-to-expand for full detail (role/area/project, timestamp,
    importance/urgency).
  - Added a mini calendar to the left sidebar (`calendar_activity()` /
    `_month_grid()`) as a fast date selector with GitHub-contribution-style
    activity density — not a full schedule view, per the spec.

- GitHub sync now prefers the Replit-managed GitHub connector (connected as
  `11p-prog`) over a manual `GITHUB_TOKEN`, mirroring the Notion connector
  pattern — added `check_github()` / `GET /integrations/github/check`.
  `GITHUB_REPOSITORY` still needs to be set before `sync_github` can commit
  (not yet configured).
- Reworked the interaction hierarchy per user feedback that the UI still
  felt like a todo app:
  - Added a persistent floating capture bar (bottom-center, always visible,
    never hidden by scroll) as the primary way to record an Event — replaces
    the old sidebar capture form. Enter submits, Shift+Enter adds a newline;
    no wizard or mandatory metadata.
  - Sidebar is now navigation-only (오늘/프로젝트/대기/지식/리뷰/보관함/설정).
  - Hero replaced with explicit operating-system-style stat tiles (오늘의
    집중/대기/차단/오늘 완료) instead of a single sentence.
  - Placeholder copy changed to invite free thought capture ("지금 떠오른
    것을 적어보세요") instead of task-creation language.
- Replaced the inline-HTML `/` route with a Jinja2 template
  (`pulda/templates/index.html`) implementing the approved Stitch visual
  design, adapted from a generic todo-list layout to an Event-lifecycle
  view per product direction:
  - Hero line is a live operational status summary ("오늘 집중 N · 대기 N ·
    차단 N · [dynamic signals]") instead of a greeting —
    `service.operations_summary()`.
  - "Today's Focus" renders Event lifecycle status pills (수집됨/계획됨/
    진행중/완료/보류/중단), not checkboxes.
  - "Waiting" (blocked-on events) is always rendered, never collapsed.
  - New "Life Balance" panel (업무/가족/건강/성장·학습) computed from active
    events via a best-effort role/area mapping —
    `service.life_balance()`. Added a `학습` classifier area to support it.
  - "Mindfulness" replaced with a rule-based "Decision Support" panel
    (`service.decision_support()`) — deterministic heuristics over real
    data (overdue/blocked/financial/stale-deferred), not an LLM call.
  - "Daily Reflection" moved out of a permanent sidebar slot into the
    daily-review flow: `reviews.reflection` column + `POST
    /reviews/reflection`, shown alongside the generated review summary.
- Added `GET /integrations/notion/check` — verifies the Notion connection
  (identity + workspace) and that the configured target page is reachable
  before allowing writes, per the handoff package's startup-validation rule.
- Extended the `events` table and API with the MVP_SPEC.md fields that were
  previously missing: `project`, `goal`, `financial_impact`, `family_impact`,
  `blocked_by`, `defer_reason`, `next_review_at`, `notion_page_id`.
- Added `GET /api/events/{id}`, `PATCH /api/events/{id}` (generic field
  update), `POST /api/events/{id}/defer` (records reason + next review date,
  sets status to `deferred`), and `GET /reviews/daily` (fetch latest review
  without regenerating it).
- Notion sync (`POST /sync/notion`) now uses the Replit-managed Notion
  connector (workspace "pulda") instead of
  a manually issued `NOTION_TOKEN`, with a fallback to `NOTION_TOKEN` for
  portability outside Replit. See `pulda/connector_client.py`.
- `AUTO_SYNC_NOTION` enabled; `NOTION_SYNC_PAGE_ID` points at the existing
  "19 Pulda Runtime MVP" Notion page.
- Added `GET /api/events/attention` — surfaces overdue, deferred, and
  blocked events in one call, completing the last missing MVP_SPEC.md
  minimum function ("show blocked/overdue/deferred items").

## 0.1.0 — Initial Replit setup

- Imported project running on Replit (FastAPI + SQLite, port 5000).
- Verified health check, UI, and test suite.
