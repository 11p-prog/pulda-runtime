# CR Status (canonical implementation index)

Notion preserves approved operating DNA, decisions, human corrections, and
dashboard status. Git preserves versioned CR acceptance criteria and
implementation history in `docs/cr/CR-XXXX.md`. Their links and status must be
reconciled through `docs/governance/OPERATING-MODEL.md`.

**Notion CR Dashboard**: https://app.notion.com/p/39be35ff69e081a4ac53fe8d1ee2f09e
(database "Pulda CR Dashboard", created under the same Pulda workspace page
used for daily review sync). Replit Link remains blank when no per-CR deep link
exists; the Builder is not a canonical source of truth.

Status values: `Draft → Review → Approved → In Progress → Implemented →
User Verified → Closed`, plus `Blocked` / `Rejected` / `Deferred` as needed.

**Implemented is not Closed.** A Builder may set a CR to Implemented only with
commit and automated regression evidence; only the user may move it to
User Verified and Closed.

**Definition of Done (per CR-0008, 2026-07-13):** a CR may be marked
`Implemented` only when its acceptance criteria are backed by an automated test
that would fail if the behavior regressed. A screenshot or manual click-through
alone is insufficient. `Related Git Commit` must carry the real commit hash.

| CR | Title | Priority | Status | Owner | Reviewer | Created | Updated |
|----|-------|----------|--------|-------|----------|---------|---------|
| CR-0000 | AI Collaboration Protocol | High | Approved | ChatGPT | User | 2026-07-12 | 2026-07-12 |
| CR-0001 | Workspace UX | High | Implemented / Verification incomplete (no automated test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0002 | Calendar = Date Context | High | Implemented (date-scoping now covered by test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0003 | Recent Events | High | Implemented (day-scoping now covered by test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0004 | Automatic Today | High | Implemented / Verification incomplete (no automated midnight-rollover test) | Replit | User | 2026-07-12 | 2026-07-13 |
| CR-0005 | Historical Import Framework | Medium | Blocked — data prerequisites | ChatGPT | User | 2026-07-12 | 2026-07-14 |
| CR-0006 | Privacy-first Architecture | High | Implemented (policy/doc only — no runtime enforcement; disclosed in CR text) | Replit | User | 2026-07-12 | 2026-07-12 |
| CR-0007 | Generic File Attachments (Import Phase 1) | Medium | Implemented (upload validation + transaction rollback now covered by test) | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0008 | External Audit Fixes + Verification Standard | High | Implemented | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0009 | Activity-Log Time Axis for the Event List | High | Implemented (covered by test) | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0010 | Remove Stray "health" Link (Scoped Interim Fix) | Medium | Implemented | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0011 | User-Managed Workspace Tabs (Replit-Style Add/Remove) | High | Reverted — superseded by CR-0012/IA-0001 per User decision | Replit | User | 2026-07-13 | 2026-07-13 |
| CR-0012 | Imported: Home and Event Feed Redesign (pulda-ux-handoff-v0.1) | High | Implemented (covered by test) | ChatGPT | User | 2026-07-13 | 2026-07-13 |
| CR-0013 | Restore the First Living Loop | High | In Progress — rule-based loop implemented; actual AI/LLM not connected; Living Loop incomplete; user verification not performed (AI connection prerequisite) | ChatGPT | User | 2026-07-13 | 2026-07-16 |
| CR-0014 | First Contextual Knowledge Case | High | Prepared locally — code/schema/API/docs/tests ready; remote commit and Runtime user verification pending | Codex | User | 2026-07-17 | 2026-07-17 |
| CR-0015 | ChatGPT Daily Activity Capture | High | In Progress — direct ingest deployed and Event ID verified; Notion relay passes locally, deployment/reauthorization/end-to-end run pending | ChatGPT | User | 2026-07-18 | 2026-07-19 |

## RFCs open for discussion
- RFC-0001 — AI Memory Structure
- RFC-0002 — Personal Data Sensitivity Layers
- RFC-0003 — Import Engine Design

## ADRs recorded
- ADR-0001 — Adopt Workspace model over Dashboard
- ADR-0002 — Event First as the core data model
- ADR-0003 — Calendar is Navigation, not the primary workspace
- ADR-0014 — AI Control Tower Portability
