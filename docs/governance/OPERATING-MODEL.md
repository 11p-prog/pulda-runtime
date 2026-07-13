# Pulda Governance Operating Model

This document governs how Pulda is changed. Runtime Event-processing behavior remains in [`../OPERATING_MODEL.md`](../OPERATING_MODEL.md).

## One control plane

Notion, Git, Runtime, conversation, and Builders are not independent product stores. They form one circulation with distinct authority.

| Object | Canonical authority | Required evidence or mirror |
|---|---|---|
| Theory, Constitution, roles, ethics | Notion | versioned Git export when implementation depends on it |
| Approved product decision | Notion decision and CR record | Git CR link and implementation mapping |
| CR acceptance criteria and implementation history | Git | Notion dashboard status and links |
| Code, schema, migration, tests, release | Git | Runtime execution evidence and Notion status |
| Event, AI interpretation, correction, action, outcome | Runtime store | export/backup; reusable correction promoted to DNA/rules |
| Emergency change | dated patch | reconciliation into Notion and Git |
| Conversation | provisional discovery and explicit user decisions | consolidation before completion |

No store replaces the others. Replit is a Builder and execution environment, not a source of truth or permanent data owner.

## Roles

- Human: creator, messenger, actor, final decisions, and real-world outcomes.
- AI: disciple, watcher, helper; interprets, detects gaps, and proposes reversible actions.
- ChatGPT / PMO & Architect: consolidates decisions, preserves continuity, issues implementation-ready CRs, audits gaps.
- Replit or another Builder: implements approved CRs, runs tests, and returns code-level and Runtime evidence.
- GitHub: versioned implementation lineage and release baseline.
- Notion: operating DNA, approved meaning, decisions, corrections, and dashboard.

## Non-negotiable rules
1. Existing canonical documents are checked before creating new structures.
2. No duplicate theory, architecture, or governance document without an explicit supersession note.
3. UI changes require UX/IA document plus CR acceptance criteria.
4. Runtime facts override assumptions.
5. New events are captured first; hierarchy is inferred later.
6. Chat memory alone is never evidence of current state.
7. A material conflict stops implementation until it is recorded and resolved.
8. Tool-only state that another Builder cannot reproduce is incomplete.
9. A disconnected document, code change, or screen is not a completed circulation.

## New-chat bootstrap

For the first Pulda request in every chat:

1. Load the relevant Notion DNA, active CR, Git files and latest commit, Runtime evidence, and any newer emergency patch or user decision.
2. Compare versions, timestamps, links, and claimed status.
3. State `confirmed`, `conflict`, `missing`, and `assumption` entries.
4. Do not plan or implement when a missing source or conflict can materially change the result.
5. Refresh the baseline after a write or a new material user decision.

`AGENTS.md`, `PROJECT_INSTRUCTIONS.md`, and the `pulda-governance` Skill enforce this bootstrap in their respective surfaces.

## Conflict resolution

Record what Notion, Git, Runtime, emergency patch, and the latest user decision each say. State the impact. Resolve through the latest explicit user decision consistent with Pulda Theory and authority boundaries. Never silently overwrite the losing side; mark it superseded, reverted, or archived and link its successor.

## Anti-fragmentation gate

Before creating an artifact, identify:

1. the canonical object it updates
2. the next consumer
3. the evidence that returns
4. where its status is visible
5. how another Builder reproduces it

If one is missing, do not create the artifact yet.

## Living synchronization protocol

Human intent or Runtime evidence → Notion DNA/decision → approved CR → Git implementation/test → Runtime execution → human correction/outcome → reusable correction → next comparable interpretation.

Exporting one store into another is not synchronization. A loop is complete only when the approved meaning is implemented and exercised, human correction is preserved, the next comparable interpretation uses it, and Notion, Git, Runtime, and CR status agree again.

## Status and completion gate

| Status | Minimum evidence |
|---|---|
| Approved | explicit user decision and acceptance criteria |
| In Progress | Builder assigned; baseline and target paths known |
| Implemented | commit plus automated regression evidence |
| User Verified | user exercised the behavior with real or accepted test data |
| Closed | all stores reconciled; no unowned follow-up |
| Blocked | exact missing authority, source, access, or evidence recorded |

Only the user may set `User Verified` or `Closed`.

## End-of-task checksum

- No material fact exists only in chat.
- No implementation exists only in Replit.
- No Notion status contradicts Git evidence.
- No Git status claims user verification.
- No data change lacks export/restore and privacy handling.
- Another Builder can identify the exact next action.

Updated: 2026-07-14
