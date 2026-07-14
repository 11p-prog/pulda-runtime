# Project AGENTS.md Template

Template status: Prepared locally  
Use: Reconcile into a project's root `AGENTS.md`; do not copy blindly or erase existing rules.

## Adoption instructions

1. Audit the existing `AGENTS.md`, project instructions, canonical documents, implementation, tests, and latest user decisions.
2. Keep valid project-specific knowledge. Mark obsolete rules with a successor rather than silently deleting them.
3. Fill every bracketed field. Remove instructional comments only after review.
4. Record the adoption diff, verification, and commit. Until the remote commit is confirmed, status is `Prepared locally`.

---

# [Project name] Agent Rules

Status: [Draft / Prepared locally / Implemented]  
Project ID: [ID]  
Repository: [owner/repository]  
Owner: [human authority]  
Last reconciled: [YYYY-MM-DD]

## Purpose and current phase

- Purpose: [why this project exists]
- Current phase: [phase]
- Current priority: [one priority]
- Explicit exclusions: [what is not in scope]

## Mandatory bootstrap

Before acting:

1. Read this file and [project instructions / README].
2. Read [Notion project record and applicable decision/CR].
3. Read [source-of-truth and sync protocol locations].
4. Read the current implementation, relevant tests, schemas/migrations, and latest commit.
5. Check newer emergency patches and explicit user decisions.
6. Record `confirmed`, `conflict`, `missing`, and `assumption`.
7. Stop when a material conflict or missing source can change the result.

Do not infer current state from chat memory alone.

## Authority and sources

| Object | Canonical source | Evidence or mirror |
|---|---|---|
| Purpose and approved decisions | [Notion location] | [Git reference/status] |
| Specifications and implementation | [Git paths] | [Notion status] |
| Runtime state | [deployment/data store] | [dated evidence] |
| Design/brand/content | [location] | [approval evidence] |
| Emergency patch | [location or none] | [reconciliation owner] |

Conflict procedure: record every source's statement and impact; do not silently choose, merge, overwrite, or create a duplicate authority.

## Project structure

- Active source: [paths]
- Tests: [paths]
- Build outputs: [paths; do not edit]
- Archives/reference only: [paths]
- Private or excluded data: [paths/types; never commit]

## Work rules

- Use `docs/AI_AX_OPERATING_PLAYBOOK.md` or the approved shared location for common AI/AX process.
- Define goal, source, constraints, deliverable, and completion conditions before execution.
- Assign one primary execution tool per work unit.
- Prefer the smallest reversible change and preserve unrelated user work.
- Use a CR for behavior changes and an ADR for durable architectural choices.
- Do not change [framework/data/privacy/authority/core direction] without explicit approval.
- For work over 30 minutes, leave [checkpoint location].
- After the same failure occurs three times, stop and perform cause analysis.

## Project commands

```text
Install: [command]
Development: [command]
Focused verification: [command]
Full verification: [command]
Build: [command]
Rollback/recovery: [command or documented procedure]
```

## Acceptance and evidence

`Implemented` requires:

- approved source decision and acceptance criteria
- changed paths and confirmed remote commit
- applicable automated verification
- reproducible execution instructions
- migration/export/restore evidence when data changes

Only the user may set `User Verified` or `Closed`. Screenshots and Builder claims are supporting evidence, not sufficient proof alone.

## Handoff and succession

Every handoff uses [AI_HANDOFF location] and reports:

- baseline and authority used
- changed files/objects and diff summary
- tests, build, Runtime, and human evidence
- environment and platform dependencies
- known issues, rollback, and exact next action

Another Builder must be able to continue without access to the previous Builder's private workspace or chat.

## Learning candidates

Record repeated corrections here before promotion:

| Candidate | Evidence count | Applicable scope | Status | Owner |
|---|---:|---|---|---|
| [rule] | [n] | [project only / cross-project candidate] | [observe/test/approved] | [owner] |

Project-specific rules remain here. Cross-project promotion requires comparable evidence from multiple projects and explicit human approval.

## Completion report

- Baseline used:
- Changed and linked:
- Evidence:
- Current status:
- Still inconsistent or blocked:
- Next smallest loop:

## Supersession record

| Previous rule/document | Status | Successor | Reason | Date |
|---|---|---|---|---|
| [item] | [active/superseded/legacy candidate] | [link/path] | [reason] | [date] |
