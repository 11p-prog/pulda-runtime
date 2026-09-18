# Pulda Git/Runtime Reconciliation — Claude Code Review Request

Date: 2026-09-11 (KST)

## Purpose

Pulda has been developed through multiple environments whose Git histories are not currently aligned:

1. this Replit workspace,
2. GitHub `11p-prog/pulda-runtime`,
3. a local folder used by Claude Code.

Do not merge, reset, checkout, commit, push, publish, migrate data, or modify files during this review. The first step is to identify what each environment contains and agree on one reconciliation strategy.

## Facts already verified in the current Replit workspace

| Item | Current Replit workspace |
|---|---|
| External Git remote | `https://github.com/11p-prog/pulda-runtime/` |
| Local branch | `main` |
| Local HEAD at review time | `7f39df7` |
| GitHub `origin/main` at review time | `b70a3b4` |
| Local upstream | Not configured |
| Shared Git ancestry | None (`git merge-base HEAD origin/main` returned no common ancestor) |
| Unique histories | Approximately 50 local commits and 108 origin commits |
| Working tree at review time | Clean |
| Replit deployment | Not deployed |
| `https://pulda-runtime.replit.app/` | 404, “This app isn't live yet” |

Commit IDs are observations, not permanent assumptions. Re-check them before making any later decision.

## High-level code comparison

| Area | Current Replit local tree | GitHub `origin/main` |
|---|---|---|
| Current product UI | Stronger/current: approved home redesign, navigable calendar, Pulda Union light/dark theme, attached logo | Older UI/runtime line |
| Project/task model | Real projects/tasks tables, event-project linking, task derivation, reserved unpopulated AI suggestions | Different and broader historical runtime evolution |
| Review/settings UI | Review approval flow and sync settings are separated | Older review/sync implementation and operational history |
| Notion daily activity | Current connector mainly exports daily review summaries | Contains daily-activity import/checkpoint and repair/migration work |
| AI provider | No real model-backed workflow in current local product line | Contains Claude/Anthropic provider code and provider tests |
| Runtime/data integrity | Simpler current SQLite runtime | Stronger daily-activity envelopes, stable keys, idempotency/checkpoint and repair history |
| Deployment/data persistence | Current Repl is not deployed; local config changed during UI work | Contains historical deployment fixes and Postgres/persistence-related governance |
| Design artifact | Contains `artifacts/mockup-sandbox` and the approved Pulda UI mockup | Does not contain the current artifact line |
| Governance/docs | Contains current UI, event, review and project/task decisions | Contains additional migration, AI-provider and deployment governance that may still be needed |

## Why a normal merge is unsafe

The Replit local `main` and GitHub `origin/main` have no common ancestor. Therefore:

- do not force-push local `main` over GitHub;
- do not use `git merge --allow-unrelated-histories` as an automatic solution;
- do not reset either side before creating durable backup refs;
- do not assume the former `.replit.app` address represents a live canonical build;
- do not run old migration or repair scripts against the only copy of a database.

The likely safe direction is to preserve GitHub history as the ancestry of a new reconciliation branch, then deliberately port the accepted local product/UI work while retaining selected origin runtime/data capabilities. This is a proposal, not an approved action.

## Claude Code: read-only inspection request

Run the following review against the local folder you currently use for Pulda. Do not make any changes.

### 1. Identify the local Git state

Report:

- absolute repository path;
- `git remote -v`;
- current branch and HEAD;
- upstream tracking branch;
- `git status --short`;
- all local branches with tracking information;
- whether the local HEAD has a merge base with GitHub `origin/main`;
- ahead/behind counts;
- whether unpushed commits, stashes, untracked files, or ignored-but-important runtime files exist.

Suggested read-only commands:

```bash
pwd
git remote -v
git status -sb
git branch -vv
git log -12 --oneline --decorate
git stash list
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
git merge-base HEAD origin/main || true
git rev-list --left-right --count HEAD...origin/main
git status --short --untracked-files=all
```

Do not run `pull`, `merge`, `rebase`, `reset`, `checkout`, `switch`, `commit`, `push`, or `clean`.

### 2. Compare Claude Code's local tree with both known lines

Identify features that exist only in Claude Code's local folder, especially:

- Notion “일일 업무 실행 로그” import and field mapping;
- checkpoint, pagination, idempotency and conflict behavior;
- Claude/Anthropic provider implementation;
- privacy/sensitivity gating before external model calls;
- daily-activity envelope/item schema and repair scripts;
- Postgres versus SQLite behavior;
- deployment configuration and production persistence;
- UI/calendar/theme/project-task changes;
- tests that prove each of the above.

For every unique capability, classify it as:

1. retain,
2. superseded,
3. requires product decision,
4. data migration only,
5. obsolete/unsafe.

### 3. Inspect non-Git state without exposing private data

Report only metadata, never values:

- database engine and database file/path type;
- whether local DB files contain data not represented elsewhere;
- relevant environment-variable names, not their values;
- whether Claude Code has modified files that Git ignores;
- whether any migration has already been applied;
- whether a deployment target is configured.

Do not print secrets, tokens, connection strings, personal log contents, or database rows.

### 4. Evaluate the proposed reconciliation direction

Assess this proposal:

1. create immutable backup refs for GitHub `origin/main`, current Replit local HEAD, and Claude Code local HEAD;
2. create a new branch descended from GitHub `origin/main`;
3. retain origin runtime/data-integrity capabilities that are still valid;
4. port the accepted Replit UI/calendar/theme/project-task work deliberately;
5. reconcile overlapping `app.py`, `service.py`, `db.py`, `connectors.py`, `.replit`, Dockerfile and tests manually;
6. test migrations only against disposable database copies;
7. push only the new reconciliation branch;
8. use a reviewed PR to update `origin/main`;
9. never force-push.

State what should change in this proposal based on the Claude Code local folder.

## Required response format

Please return one Markdown report with these sections:

```markdown
# Claude Code Pulda Reconciliation Review

## 1. Local Repository Identity
| Item | Value |

## 2. Relationship to GitHub origin/main
- Merge base:
- Ahead/behind:
- Unpushed work:

## 3. Claude-Local-Only Capabilities
| Capability | Files/commits | Classification | Reason |

## 4. GitHub-Origin-Only Capabilities
| Capability | Files/commits | Classification | Reason |

## 5. Replit-Local Capabilities to Preserve
| Capability | Expected integration impact |

## 6. Database and Migration Risks
- Metadata only; no private data or secrets.

## 7. Deployment and Runtime Findings

## 8. Recommended Canonical Baseline

## 9. Proposed Reconciliation Sequence
- Include explicit backup refs and stop/go checkpoints.

## 10. Decisions Required From the User

## 11. Commands That Must Not Be Run Yet
```

## Stop condition

After producing the report, stop. Do not begin reconciliation until the user has shared the report back with the Replit agent and explicitly approved a final integration plan.