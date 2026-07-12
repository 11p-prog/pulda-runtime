# Pulda Runtime MVP

A Python/FastAPI app for capturing free-text "events", auto-classifying them into
tasks (role/area/urgency/importance/status), storing them in SQLite, and
generating a daily execution plan and review. Optional Notion and GitHub sync
are available but disabled by default.

## Stack
- Python 3.11, FastAPI + Uvicorn, SQLite (file-based), APScheduler for periodic
  self-review jobs.
- Server-rendered HTML UI at `/` plus a JSON REST API under `/api/*`.

## Running on Replit
- The `Start application` workflow runs `python -m pulda.app`, which serves on
  all interfaces, port 5000 (overridden via `PULDA_PORT` in `.env` for the
  Replit preview, which requires port 5000).
- Configuration lives in `.env` (copied from `.env.example`) plus shared env
  vars (`AUTO_SYNC_NOTION`, `NOTION_SYNC_PAGE_ID`) set via Replit env vars.
- SQLite data is stored at `data/pulda.db` (gitignored).

## Notion sync
- Notion sync uses the Replit-managed Notion connector (workspace "pulda")
  instead of a manually issued `NOTION_TOKEN` — see
  `pulda/connector_client.py` for the identity/proxy client and
  `pulda/connectors.py::sync_notion`/`check_notion` for the call sites.
- `AUTO_SYNC_NOTION=true` and `NOTION_SYNC_PAGE_ID` (the "19 Pulda Runtime MVP"
  page) are set as shared env vars. Daily reviews append as a paragraph block
  under that page.
- `GET /integrations/notion/check` verifies the connection and target page
  before any write — added per the `pulda-replit-handoff` package's
  validation rule (`PROJECT_REGISTRY.md`).
- GitHub sync (`sync_github`) is still off (`AUTO_SYNC_GITHUB=false`) — needs
  `GITHUB_TOKEN`/`GITHUB_REPOSITORY` if the user wants it later.

## Handoff package (attached_assets/pulda-replit-handoff...)
- A separate handoff package (AGENTS.md, PROJECT_REGISTRY.md, docs/*) was
  uploaded describing a bigger target architecture where Notion databases
  (Events/Logs/Decisions) are the operational source of truth, not just a
  page receiving review summaries.
- User chose an incremental approach: adopted the startup Notion validation
  endpoint and the missing `Event` fields from `docs/MVP_SPEC.md` first,
  without migrating storage off SQLite or creating Notion databases yet.
- Not yet done: `NOTION_EVENTS_DB_ID`/`NOTION_LOGS_DB_ID`/`NOTION_DECISIONS_DB_ID`
  (no Notion databases created), Notion-as-source-of-truth data flow, and the
  broader `AGENTS.md` operating rules (deferred/blocked/abandoned/someday
  distinctions, full audit-log shape with actor/previous-state/reason). Revisit
  if the user wants to continue down that path.

## UI redesign (Stitch baseline)
- The `/` page was rebuilt from a plain HTML table into a calm, whitespace-
  generous design (Inter font, Tailwind via CDN, soft-shadow cards) based on
  a Stitch design proposal the user approved as visual baseline, but adapted
  to Pulda's Event-lifecycle model rather than a todo-app metaphor — see
  `CHANGELOG.md` for the specific content/IA deviations from the raw Stitch
  proposal (operational-status hero, always-visible Waiting, Life Balance,
  Decision Support, reflection-in-review-flow).
- Life Balance's four buckets (업무/가족/건강/성장·학습) are a best-effort
  heuristic mapping from the existing `role`/`area` fields
  (`service._balance_bucket`), not a first-class data model — revisit if the
  domain model gains explicit life-area fields.
- Tailwind is loaded via CDN for now (browser logs a "not for production"
  warning) — acceptable at this MVP/infancy stage; switch to a built
  Tailwind pipeline if/when the app moves toward production packaging.
- GitHub sync is now wired up like Notion: connected via the Replit GitHub
  connector (account `11p-prog`), target repo `11p-prog/pulda-runtime`
  (`GITHUB_REPOSITORY`/`GITHUB_BRANCH` shared env vars), `AUTO_SYNC_GITHUB=true`.

## UX v2: workspace model (VS Code/Replit-style, not a dashboard)
- The `/` page is organized into workspace tabs (query/form param `ctx`):
  `today`, one `project:<name>` tab per distinct `events.project` value,
  `role:성당` (Church), `role:가족` (Family), and a `knowledge` placeholder
  (feature not built yet). `pulda.service.context_workspace(ctx)` scopes
  stats/plan/attention/table to the active tab; `context_events`/
  `distinct_projects` back it.
- Context-first capture: the persistent bottom capture bar submits the
  active `ctx`; `create_event(..., role_override=...)` auto-tags the Event
  with the tab's role or project so the user rarely needs manual
  categorization (per the UX v2 spec in `attached_assets/`).
- Left sidebar now also has a mini calendar (`calendar_activity`/
  `_month_grid`) — a fast date selector with contribution-style activity
  density, not a full schedule view. Sidebar nav items (오늘/프로젝트/대기/
  지식/리뷰/보관함/설정) are unchanged from UX v1 and are distinct from the
  center workspace tabs.
- A "최근 Event" (Recent Events) panel is mandatory per the spec — always
  shown, chronological (not priority-sorted), click-to-expand for detail.

## Review v3: date is also a workspace context
- Two independent context axes: domain (`ctx`, as above) and date
  (`selected_date`, via `cal_date` query/form param). `context_workspace(ctx,
  selected_date)` scopes everything to both. Picking a calendar date is a
  real context switch — the center view shows that day's plan/stats/events/
  review, not just a highlighted cell.
- Live-only sections (Waiting/Overdue/Deferred) render only when
  `is_today` — a historical date shows a day-scoped record (`plan` becomes
  "주요 항목" for that day) instead of pretending to be a live dashboard.
  `review_for_date()` looks up that date's review instead of always "latest".
- "Today" auto-follows real local time: unpinned views (no `cal_date` in the
  URL) poll the browser clock and reload at local midnight; a pinned
  historical date is left alone until the user clicks "Today로 돌아가기".
- `life_balance()` omits any bucket with zero real data — no invented
  0건/0% placeholder metrics (Review v3 #3).
- Privacy architecture principles and current gaps are documented in
  `docs/PRIVACY_ARCHITECTURE.md` (Review v3 #5/#7) — read before adding any
  feature that sends Event data to an external AI provider.
- Historical import (Review v3 #4) is deferred to Phase 2 and must NOT be
  built as a Google-Docs-specific feature — design it as a provider-
  independent Import Pipeline (Google Docs, Markdown, Notion Export, TXT,
  PDF, future sources all as adapters behind one extraction interface).
  Design placeholder (no code yet) is in `docs/IMPORT_PIPELINE.md`. The
  user already decided: rule-based classifier only, no external AI call,
  for journal→Event extraction.

## Product philosophy (from the ChatGPT architect's design conversation)
- "Pulda does not visualize widgets. Pulda visualizes the user's current
  operating context." Navigation (calendar, tabs) exists to find;
  Workspace (center pane) exists to work; Conversation (capture bar) exists
  to capture. Any new screen/feature should be justified by which of these
  three roles it serves — a widget that doesn't represent the user's actual
  state is a placeholder and should be removed (this is *why* the zero-data
  Health bucket was removed, not just a one-off fix).
- Pulda's own definition, from the same conversation: it is not a "to-do
  management" system — it operates a workspace where Time Context
  (Today/Yesterday/a selected date) and Domain Context (Business/Family/
  Church/Personal/Knowledge) meet. This is why date selection is a context
  switch (loads that date's real workspace), not a filter on a dashboard.

## AI collaboration protocol (CR-0000) — CR / ADR / RFC document system
- The user works with a separate ChatGPT "Chief Architect" that issues
  Change Requests; Replit (this agent) is the "Runtime Engineer" —
  implements, tests, deploys, and updates documentation after
  implementation. Full protocol: `docs/cr/CR-0000.md`.
- **Three document types**, each with one file per item, edited
  cumulatively (never forked into a new file for the same number):
  - `docs/cr/CR-XXXX.md` — Change Request ("무엇을 바꿀 것인가"). Template:
    CR Number, Title, Background, Problem, Goals, Requirements, Acceptance
    Criteria, Future Considerations, Affected Components, Status, Related
    CR, Related Notion, Related Git Commit.
  - `docs/adr/ADR-XXXX.md` — Architecture Decision Record ("왜 이렇게
    설계하기로 결정했는가"). Template: Title, Status, Context, Decision,
    Consequences.
  - `docs/rfc/RFC-XXXX.md` — Request for Comments ("아직 결정되지 않았지만
    함께 검토할 주제") — open topics, not build directives. Graduates into
    CR(s)/an ADR once a direction is chosen; never implemented directly.
- **Git is the source of truth** for all three; `docs/cr/STATUS.md` is the
  canonical status index. **Notion is an operations dashboard only** — it
  mirrors CR Number/Title/Priority/Status/Owner/Reviewer/Created/Updated/
  GitHub Link/Replit Link, never the CR content itself.
- **Unified status lifecycle**: `Draft → Review → Approved → In Progress →
  Implemented → User Verified → Closed` (plus `Blocked`/`Rejected`/
  `Deferred`). **Critical rule: Implemented ≠ Closed.** This agent may set
  a CR to Implemented after building+testing it; only the user's
  verification can move it to User Verified → Closed. Never self-close a CR.
- CR files uploaded to `attached_assets/` should be copied into `docs/cr/`
  (or the matching CR-XXXX.md updated in place) so they live in the
  canonical GitHub-synced location, not only the ephemeral upload folder.
- Status as of this turn: CR-0001/0002/0003/0004/0006 = Implemented
  (awaiting User Verified); CR-0005 (Historical Import Framework) =
  Deferred to Phase 2 by explicit user direction — design captured in
  `docs/IMPORT_PIPELINE.md` and `docs/rfc/RFC-0003.md`. Three ADRs recorded
  (`docs/adr/ADR-0001..0003.md`: Workspace-over-Dashboard, Event First,
  Calendar-is-Navigation). Three RFCs open (`docs/rfc/RFC-0001..0003.md`:
  AI memory structure, personal-data sensitivity layers, import engine
  design) — none are build directives yet.

## User preferences
- Imported project: keep the existing structure/stack as-is; do not restructure
  or migrate frameworks without being asked.
- Product roadmap: current phase is real-world daily use on the small
  SQLite+FastAPI MVP ("infancy" phase). The user plans to hand the project to
  Codex later for the larger architecture evolution (e.g. Notion-as-source-of-
  truth, full AGENTS.md operating rules). Until then, keep changes small and
  incremental based on real usage feedback — do not proactively redesign or
  migrate architecture.
