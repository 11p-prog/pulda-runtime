---
name: Pulda navigation model (post tab-bar revert)
description: Pulda has no central Event/Task/Goal/Project tab bar — Home is a single Activity Feed, Projects is its own nav destination, per IA-0001/CR-0012.
---

Two tab-bar designs were tried and both were rejected by the user — don't
reintroduce a center context-switcher (fixed categories *or* user-managed
add/remove tabs) without re-confirming with the user first:
1. A fixed role/project/knowledge tab set (original design) — rejected as
   too rigid.
2. CR-0011's Replit-style user-managed tabs (add/remove via `workspace_tabs`
   table) — built, then reverted when the user's ChatGPT PMO/architect sent
   IA-0001 (`docs/ia/IA-0001-main-navigation.md`) mandating "navigate by
   purpose, not database entity type," landed as CR-0012.

**Current model (CR-0012/IA-0001, since 2026-07-13):** Home (`/`) is a single
Activity Feed with no context switcher — it always behaves like the old
`ctx="today"` view. The only remaining context axis is the date, via the
sidebar mini-calendar (`?cal_date=`). Projects is a real top-level nav item
(`/projects` list, `/projects/{name}` detail) backed by the same
`distinct_projects()`/`context_events("project:<name>")` machinery the old
project tabs used — the data model didn't change, only how it's reached.
Routine/Knowledge/Archive/Settings remain "준비중" placeholders in the
sidebar; role stays an inferred per-event label only, never a nav concept.

**Why:** two rejected designs in a row means the *concept* of a central
tab/context switcher is the recurring failure mode here, not any one
implementation — treat "no central entity-type tab bar" as a standing
constraint for this app, not a one-off preference.

**How to apply:** if asked to add navigation, check whether it's a new
top-level *purpose* (add to the fixed sidebar list, like Projects) vs. a new
filterable slice of Events (extend `service._ctx_clause`/`context_events`
and reach it through a dedicated route+template, not a tab). Never bring
back a `ctx` query/form param threaded through every route — that pattern is
gone along with `workspace_tabs`.
