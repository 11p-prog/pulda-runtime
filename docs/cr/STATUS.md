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

| CR | Title | Priority | Status | Owner | Reviewer | Created | Updated |
|----|-------|----------|--------|-------|----------|---------|---------|
| CR-0000 | AI Collaboration Protocol | High | Approved | ChatGPT | User | 2026-07-12 | 2026-07-12 |
| CR-0001 | Workspace UX | High | Implemented | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0002 | Calendar = Date Context | High | Implemented | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0003 | Recent Events | High | Implemented | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0004 | Automatic Today | High | Implemented | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0005 | Historical Import Framework | Medium | Deferred | — | — | 2026-07-12 | 2026-07-12 |
| CR-0006 | Privacy-first Architecture | High | Implemented | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0007 | Generic File Attachments (Import Phase 1) | Medium | Implemented | Replit | User | 2026-07-13 | 2026-07-13 |

## RFCs open for discussion
- RFC-0001 — AI Memory Structure
- RFC-0002 — Personal Data Sensitivity Layers
- RFC-0003 — Import Engine Design

## ADRs recorded
- ADR-0001 — Adopt Workspace model over Dashboard
- ADR-0002 — Event First as the core data model
- ADR-0003 — Calendar is Navigation, not the primary workspace
