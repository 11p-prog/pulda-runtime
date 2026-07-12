# CR Status (canonical index — Git is source of truth)

Notion mirrors only the columns below (CR Number, Title, Priority, Status,
Owner, Reviewer, Created, Updated, GitHub Link, Replit Link) as an
operations dashboard. CR content itself lives only here, in
`docs/cr/CR-XXXX.md`, edited cumulatively.

**Notion CR Dashboard**: https://app.notion.com/p/39be35ff69e081a4ac53fe8d1ee2f09e
(database "Pulda CR Dashboard", created under the same Pulda workspace page
used for daily review sync). Rows for CR-0000..CR-0006 are populated with
Priority/Status/Owner/Reviewer/Created/Updated/GitHub Link. Replit Link
column left blank — no per-CR Replit deep link exists yet; the whole
project is a single Repl (11p1/pulda-runtime-mvp-v01).

Status values: `Draft → Review → Approved → In Progress → Implemented →
User Verified → Closed`, plus `Blocked` / `Rejected` / `Deferred` as needed.

**Implemented is not Closed.** Replit may set a CR to Implemented; only the
user's verification can move it to User Verified → Closed.

**Definition of Done (per CR-0008, 2026-07-13):** a CR may be marked
`Implemented` only when its acceptance criteria are backed by an
automated test that would fail if the behavior regressed — a screenshot
or manual click-through alone is not sufficient. `Related Git Commit`
must carry the real commit hash at the time of that status change. This
bar was applied retroactively below: CRs whose acceptance criteria are
now covered by `tests/test_runtime.py` are `Implemented`; CRs with a real
gap between claim and test coverage are marked `Implemented / Verification
incomplete` until closed.

| CR | Title | Priority | Status | Owner | Reviewer | Created | Updated |
|----|-------|----------|--------|-------|----------|---------|---------|
| CR-0000 | AI Collaboration Protocol | High | Approved | ChatGPT | User | 2026-07-12 | 2026-07-12 |
| CR-0001 | Workspace UX | High | Implemented / Verification incomplete (no automated test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0002 | Calendar = Date Context | High | Implemented (date-scoping now covered by test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0003 | Recent Events | High | Implemented (day-scoping now covered by test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0004 | Automatic Today | High | Implemented / Verification incomplete (no automated midnight-rollover test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0005 | Historical Import Framework | Medium | Deferred | — | — | 2026-07-12 | 2026-07-12 |
| CR-0006 | Privacy-first Architecture | High | Implemented (policy/doc only — no runtime enforcement; disclosed in CR text) | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0007 | Generic File Attachments (Import Phase 1) | Medium | Implemented (upload validation + transaction rollback now covered by test) | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0008 | External Audit Fixes + Verification Standard | High | Implemented | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0009 | Activity-Log Time Axis for the Event List | High | Implemented (covered by test) | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0010 | Remove Stray "health" Link (Scoped Interim Fix) | Medium | Implemented | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0011 | User-Managed Workspace Tabs (Replit-Style Add/Remove) | High | Reverted — superseded by CR-0012/IA-0001 per User decision | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0012 | Imported: Home and Event Feed Redesign (pulda-ux-handoff-v0.1) | High | Implemented (covered by test) | ChatGPT | User | 2026-07-13 | 2026-07-13 |

## RFCs open for discussion
- RFC-0001 — AI Memory Structure
- RFC-0002 — Personal Data Sensitivity Layers
- RFC-0003 — Import Engine Design

## ADRs recorded
- ADR-0001 — Adopt Workspace model over Dashboard
- ADR-0002 — Event First as the core data model
- ADR-0003 — Calendar is Navigation, not the primary workspace
