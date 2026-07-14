# Pulda AI/AX Operating Playbook

Status: Prepared locally  
Authority: Notion `26 Operating Model` and `ADR-011`  
Prepared: 2026-07-15  
Applies to: Pulda OS and Pulda-managed projects

## Purpose

This Playbook turns approved Pulda AI/AX decisions into a reproducible Git operating standard. It governs how work is framed, assigned, executed, verified, handed off, learned from, and—only after evidence—promoted or automated.

AI output alone is not completion. Work must reach its next consumer and return evidence appropriate to its status.

## Authority and document relationships

| Document or system | Role | Relationship to this Playbook |
|---|---|---|
| Notion `26 Operating Model` | Approved operating DNA | Primary authority for roles, process, maturity, and status meaning |
| Notion `ADR-011` | Durable AI/AX decision | Primary authority for the standard loop and promotion order |
| Repository `AGENTS.md` | Project-specific Builder rules | Takes precedence for paths, commands, domain constraints, and local safety; must not weaken this Playbook's evidence gates |
| `SOURCE_OF_TRUTH.md` | Cross-store authority and conflict resolution | Upstream governance control; resolve conflicts before execution |
| `SYNC_PROTOCOL.md` | Decision-to-use circulation and status gates | Upstream lifecycle control; determines when work advances beyond local preparation |
| This Playbook | Common AI/AX execution standard | Translates approved governance into a reusable work method |
| `templates/PROJECT_AGENTS_TEMPLATE.md` | Project rule scaffold | Used to create or reconcile a project's `AGENTS.md`; never overwrites project knowledge silently |
| `templates/AI_TASK_BRIEF.md` | Pre-execution contract | Captures the minimum approved work unit before an AI or Builder acts |
| `templates/AI_HANDOFF.md` | Return-evidence contract | Transfers results, verification, risks, and exact next action to the next consumer |

`SOURCE_OF_TRUTH.md` and `SYNC_PROTOCOL.md` are not present in this repository at preparation time. Their current candidate versions belong to the 2026-07-14 `pulda-runtime` Phase 0 emergency patch. They are treated as upstream governance candidates, not copied or silently re-authored here. When their real Git locations and commits are confirmed, replace this note with stable repository links.

The existing root `AGENTS.md` remains the active project-specific rule set for the Pulda website repository. This Playbook supplements it; it does not supersede or replace it.

## Non-negotiable operating principles

1. Human is the creator, messenger, actor, final priority setter, and acceptance authority.
2. AI is a disciple, watcher, and helper. It may interpret, propose, implement within scope, verify, and report; it does not silently expand authority.
3. Every task starts by confirming goal, source, constraints, deliverable, and completion conditions.
4. One primary execution tool owns one work unit. Additional AI tools default to review or falsification, not parallel regeneration.
5. Existing canonical objects are extended before new documents or structures are created.
6. Material conflict between Notion, Git, Runtime, emergency patches, or explicit user decisions stops implementation until recorded and resolved.
7. A result trapped in one Builder, chat, or proprietary workspace is not complete.
8. Repeated correction may become a project `AGENTS.md` rule. Only cross-project evidence may promote it to a common Playbook or Skill.
9. Unverified procedures are not automated.

## AI/AX maturity ladder

| Level | Name | Minimum evidence to enter | Exit condition |
|---|---|---|---|
| L0 | Assistance | One-off request and human review | Repetition or reusable value is observed |
| L1 | Standardization | Repeated prompt/checklist with recorded outcomes | Stable inputs, outputs, and checks are defined |
| L2 | Project operation | Project instructions, sources, constraints, and handoff path exist | Repeated project use proves the rule |
| L3 | Skill | Procedure and judgment rules are validated across applicable work | Versioned Skill passes defined evaluations |
| L4 | Connector | Authority, permissions, recovery, and data ownership are defined | Connection is reproducible and monitored |
| L5 | Automation | Human-repeated procedure is stable and reversible | Automated runs meet quality and recovery gates |
| L6 | Limited autonomy | Error cost is low; stop, rollback, and escalation work | Continued evidence supports the bounded scope |

Do not skip levels. Promotion is a decision backed by evidence, not a label applied at creation.

## Standard work loop

### 1. Bootstrap

- Read relevant Notion decisions, repository `AGENTS.md`, canonical Git documents, current implementation/tests, newer emergency patches, and explicit user corrections.
- Record a compact baseline with `confirmed`, `conflict`, `missing`, and `assumption` entries.
- Identify the canonical object being updated, its next consumer, return evidence, visible status location, and Builder succession path.

### 2. Brief

Use `templates/AI_TASK_BRIEF.md` for work that is multi-step, costly, externally handed off, or expected to take at least 30 minutes. A brief must define:

- goal
- authoritative sources
- constraints and exclusions
- exact deliverables and affected paths
- primary execution tool and reviewer/falsifier, if any
- acceptance and verification conditions
- rollback or recovery needs
- status target

Simple, low-risk, reversible work may proceed immediately after these fields are confirmed in context.

### 3. Risk branch

- **Simple / low-risk / reversible:** execute the smallest unit, self-review, verify, and return evidence.
- **Complex / high-risk / irreversible:** audit current state, define acceptance criteria and rollback, obtain plan approval, then execute.
- **New tool or method:** record a Tool Assignment Hypothesis and test it in Pulda Lab. Measure time, direct cost, quality, review burden, failure recovery, and handoff cost.

### 4. Execute

- Assign exactly one primary execution tool.
- Keep changes within the approved unit and affected paths.
- Prefer scoped edits over full regeneration.
- Preserve unrelated user work and predecessor history.
- Leave a checkpoint when work exceeds 30 minutes.
- Do not repeat the same failure three times without stopping for cause analysis.

### 5. Verify

Use the narrowest relevant checks first, then broader regression checks proportional to risk. Evidence may include:

- document structure and link checks
- Git diff and whitespace checks
- automated tests or build results
- Runtime execution evidence
- data migration, backup, restore, and export evidence
- reviewer/falsifier findings
- human review or real-use correction

A plausible answer, generated file, screenshot, or Builder claim is not sufficient evidence by itself.

### 6. Handoff

Use `templates/AI_HANDOFF.md` when another person, Builder, session, or project consumes the result. Include changed paths, decisions applied, verification results, unresolved conflicts, safe rollback, and one exact next action.

### 7. Reconcile and learn

- Return evidence to the applicable Notion, Git, Runtime, CR, or project status record.
- Separate one-time exceptions from reusable corrections.
- Put repeated project corrections into the project's `AGENTS.md` candidate list.
- Promote to a common Playbook or Skill only after comparable success across multiple projects and explicit human approval.
- Automate only after the procedure is stable, observable, reversible, and recoverable.

## Tool assignment defaults

These are defaults, not permanent vendor commitments.

| Role | Default responsibility |
|---|---|
| Human | Purpose, priority, approval, action, real-use verification |
| ChatGPT | PMO, architecture, requirements, CR/WBS, handoff, status audit |
| Notion | Approved operating DNA, decisions, corrections, project status |
| GitHub | Specifications, code, tests, commits, releases |
| Codex | Repository audit, scoped modification, tests, diff, implementation evidence |
| Replit | Cost-effective early Runtime, deployment, and use validation when available |
| Stitch / Canva | UI candidates and client-review visuals |
| NotebookLM | Research over a fixed source bundle |
| Make / automation tools | Stable, repeatedly verified procedures only |

Any changed assignment starts as a hypothesis under ADR-009 and is evaluated through Pulda Lab under ADR-010.

## Status and completion gates

| Status | Meaning in this workflow |
|---|---|
| Notion Approved | Human-approved operating meaning or decision exists in Notion |
| Git Pending | Approved decision has not yet been confirmed in a Git commit |
| Prepared locally | Files exist in the user's local repository with diff and validation available; no remote commit is claimed |
| Implemented | Remote commit and applicable automated evidence are confirmed |
| User Verified | User has exercised or explicitly accepted the result |
| Closed | Authorities, implementation, evidence, and follow-ups are reconciled |
| Runtime Not Applicable | No Runtime behavior or execution evidence is relevant to the work unit |

Only the user may establish `User Verified` or `Closed`. Local preparation must never be reported as `Implemented`.

## Cost and rework record

For material work, capture:

| Measure | What to record |
|---|---|
| Time | Briefing, execution, review, recovery, and handoff time |
| Direct cost | Credits, subscriptions, external services, and human contractor cost |
| Quality | Acceptance checks passed, defect severity, and correction count |
| Rework | Regeneration, reverted work, duplicated effort, and cause |
| Recovery | Time and steps needed to resume or roll back |
| Succession | Whether another Builder reproduced or continued the work |

This evidence feeds the later Tour Thai evaluation and determines whether a rule remains local, enters a project `AGENTS.md`, becomes a common Skill, or is rejected.

## Concurrent circulation and operating capacity

Real work does not wait for one task to finish before another begins. Events and projects move concurrently through preparation, execution, waiting, return, review, re-entry, and completion. Pulda must preserve each loop without assuming that every loop deserves continuous attention.

The Evony expedition example is an operating metaphor, not a Pulda domain vocabulary: a long-running expedition consumes forces and supplies while the operator continues gathering, upgrading, defending, and making political decisions. A poorly judged expedition can destroy scarce capacity and impair every other operation.

Translate the metaphor into AI/AX controls as follows:

| Expedition metaphor | AI/AX operating control |
|---|---|
| Order an expedition | Delegate work or start execution |
| Troops and supplies | Time, money, AI credits, people, and attention |
| Travel time | Processing time and external-response latency |
| Home base | Work and life the human must continue to operate directly |
| Reconnaissance | Source audit, feasibility check, and risk assessment |
| Return | Result delivery and handoff |
| Retreat | Cancel, de-scope, pause, or recover |
| Force loss | Cost loss, destructive rework, or failed recovery |
| Expedition limit | Number of concurrent results the human can retrieve, review, and decide on |

### Dispatch gate

Before delegating high-cost or long-running work, confirm:

- objective, authoritative source, and approved scope
- resources at risk and maximum acceptable loss
- expected return time or return condition
- evidence that must return with the result
- cancellation, de-scoping, and recovery path
- impact on other active projects and human obligations
- named person responsible for retrieval and review

Do not start a delegation that has no defined return condition, return evidence, or next consumer.

### Operational states

Do not collapse all delegated work into `In Progress`. Track the smallest useful distinction:

1. `Preparing` — objective, source, scope, resources, and recovery are being checked.
2. `Executing` — a named person or tool is actively performing the work.
3. `Waiting` — execution depends on an external response, elapsed time, build, approval, or condition.
4. `Return Due` — a result is available or expected and has a named retrieval/review owner.
5. `Reviewing` — returned evidence is being checked against acceptance conditions.
6. `Re-entering` — corrected or reduced work is deliberately sent through another cycle.
7. `Paused / Withdrawn` — capacity is protected through pause, cancellation, de-scope, or abandonment with a recorded reason.
8. `Completed` — the result has reached its consumer and applicable evidence and follow-up are reconciled.

These are operating-model candidates, not yet fixed Runtime schema values. Runtime adoption requires Tour Thai evidence and a separate approved CR.

### Retrieval capacity is the concurrency limit

AI production capacity is not the same as human operating capacity. If AI can generate ten results but the human can retrieve, review, and decide on only two, the effective concurrency limit is two.

- Limit concurrent delegation by human retrieval and review capacity, not tool throughput.
- While long-running work is waiting, prefer bounded, low-risk work that will not create an unreviewable return queue.
- When return demand exceeds capacity, pause dispatch, retrieve the highest-risk or most time-sensitive result, and re-evaluate the remaining loops.
- Measure review backlog, delayed retrieval, and abandoned outputs as rework and operating-cost evidence.

This section is approved operating guidance. Promotion into a common Skill or automation remains blocked until practical evidence is collected from Tour Thai and at least one comparable project.

## Required end report

Every material AI/AX task ends with:

- baseline used
- changed and linked objects/files
- diff summary
- verification and Runtime evidence, or `Not Applicable`
- current status
- unresolved conflict, risk, or missing evidence
- next smallest loop

## Current rollout order

1. Pulda Git Playbook and templates
2. Codex global `AGENTS.md`
3. Active-project canonical-document audit
4. First practical application to Tour Thai
5. Time, cost, and rework evaluation
6. Promotion of validated rules to common Skills only
7. Automation of stable work only
8. Succession of projects from the other two accounts

Do not advance a later step merely because its artifact can be generated. Advance when the preceding step returns the evidence required by this Playbook.
