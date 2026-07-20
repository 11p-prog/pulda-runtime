# Pulda Runtime Help

## Event date and state

- The selected date in the left calendar is the Event's occurrence date. The
  actual input time is preserved separately.
- New Events start as **기록됨**. Where they came from (direct input,
  ChatGPT, API, import, or connector) is shown separately from status.
- Status is optional during capture. Select one or more rows in the Event list
  to change status in bulk.

## Repeating Events

Repeating Events have one series rule and independent dated occurrences. The
series may be active, paused, or ended; a dated occurrence may be scheduled,
recorded, skipped, or cancelled. A repeating series is not displayed as
continuously "in progress," and the Runtime does not pre-create an unlimited
future.

## Central workspace

Home is the permanent date-based Event tab. **+** opens a temporary **NEW** tab
whose entire center workspace presents descriptive cards for Life, Work,
Community, Statistics, and Settings. Selecting a card adds that view as a tab.
Closing a tab closes only the view and never deletes Event data. The tab strip
wraps without creating its own horizontal scrollbar.

The left panel is a favorites area for frequently used destinations, not a
separate screen hierarchy. Today remains the permanent Home context, while
Projects is a shortcut into **Work > Projects**. Inside a screen, breadcrumbs
move between depths. Screens that are not implemented are not shown as fake
NEW-tab choices or disabled favorites.

This is the living user-facing guide for behavior that exists in the current
Runtime. Update it in the same Git change whenever visible behavior or a user
constraint changes.

## Capture an Event

- Enter natural language in the bottom capture bar. Pulda stores the original
  text first and infers role, area, kind, urgency, and importance afterward.
- One capture currently creates one Event. Multi-Event splitting, candidate
  review, merge, exclusion, and approval are planned but not implemented.
- Attachments currently accept PDF and common image formats up to the configured
  size limit (20 MB by default). The file is stored as evidence; text extraction
  and Event-candidate generation are not implemented yet.

## Run the first Living Loop by API

The current UI does not expose interpretation and correction controls yet. A
reproducible backend loop is available through these endpoints:

1. `POST /api/events` — preserve the original Event.
2. `POST /api/events/{event_id}/interpretations` — create a versioned
   interpretation with model, prompt, DNA version, confidence, and source
   evidence.
3. `POST /api/interpretations/{interpretation_id}/corrections` — store a human
   correction. Use `scope: one_time` for an exception or `scope: reusable` with
   `reusable_match_text` to create a rule for comparable Events.
4. `POST /api/events/{event_id}/outcomes` — record the real result.
5. `POST /api/events/{event_id}/follow-ups` — create a follow-up proposal tied
   to that outcome.
6. Create and interpret a comparable Event. Its `applied_rule_ids` shows whether
   the reusable correction affected the next interpretation.

This is backend execution evidence, not user verification. The classifier is
still rule-based and there is no live LLM provider or human-review UI.

## Capture and retrieve one knowledge source by API

- `POST /api/knowledge-sources` creates an ordinary Event and links source
  metadata. Required fields are `canonical_url`, `title`, `summary`, and
  `relevance_note`; project, tags, related contexts, storage information, hash,
  and extra metadata are optional.
- The canonical URL prevents duplicate Events when the same item is captured
  again.
- `GET /api/knowledge-sources/relevant?query=...&project=...` retrieves sources
  whose title, summary, relevance, tags, or related contexts match the query.
- `archival_status: reference_only` means only the original URL is currently
  preserved. Change the storage URI/status only after a real user-owned
  Drive/local copy exists. Pulda must not imply that an original was archived
  when it was not.
- This first case is API-only. It does not import the historical backlog,
  extract full text, call external AI, or synchronize files offline.

## Register a ChatGPT Daily Activity Event

- `POST /api/daily-activities` creates one Event for an activity date and
  source channel, then appends typed items without duplicating repeated input.
- Each item is an `instruction`, `decision`, `work_result`, `action_candidate`,
  or `hold`, with an optional project, source reference, and review state.
- `GET /api/daily-activities/{activity_date}` returns the Event ID, source
  coverage, access gaps, and structured items as portable JSON.
- Set `PULDA_DAILY_ACTIVITY_INGEST_TOKEN` before exposing these endpoints
  outside a trusted local environment and send it as a Bearer token.
- The payload must set `privacy_reviewed: true`; otherwise Runtime rejects it
  before creating an Event.
- The API stores only the supplied summaries. It does not read ChatGPT
  transcripts, credentials, or account-wide conversation history by itself.
- The scheduled adapter uses the canonical Notion queue page configured by
  `NOTION_DAILY_ACTIVITY_QUEUE_PAGE_ID`. With
  `AUTO_INGEST_DAILY_ACTIVITY_QUEUE=true`, the 22:40 Runtime cycle reads JSON
  code blocks whose `kind` is `pulda-daily-activity` and registers them through
  the same idempotent service. Repeated pulls do not duplicate Events or items.
  The ten-minute offset prevents the Runtime pull from racing the 22:30
  ChatGPT cutoff task; override it with `DAILY_ACTIVITY_PULL_HOUR` and
  `DAILY_ACTIVITY_PULL_MINUTE` when needed.
- `POST /integrations/notion/daily-activities/pull` performs the same pull on
  demand and requires the daily activity Bearer token.

## Runtime database selection

- Deployment uses PostgreSQL automatically when `DATABASE_URL` is present.
- Local development and tests continue to use the SQLite file configured by
  `PULDA_DB_PATH` when `DATABASE_URL` is absent.
- `/api/health` reports `database_backend` so deployment evidence can confirm
  which store is active without exposing connection credentials.
- On Replit Autoscale, do not use the SQLite file as the operational source of
  truth. A valid persistence proof creates an Event, redeploys, retrieves the
  same Event ID, and replays the envelope without duplication.

## Change and delete records

- Normal delete is a soft delete: the Event disappears from active lists but
  remains stored and a deletion transition appears in history.
- Hard delete permanently purges an accidental duplicate and its attachment and
  status history. Use it only when no record should remain.
- Restore-window controls, Event binding/unbinding, history filters, and copying
  an old record into a new Event are planned but not implemented.

## First-use guidance rule

Essential concepts such as original preservation, one-time versus reusable
correction, soft versus hard delete, and approval before multi-Event creation
must be taught inline through a tooltip or short guide when their UI is added.
The Help page remains the detailed reference.
