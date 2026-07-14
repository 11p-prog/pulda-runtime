# Pulda Runtime Agent Rules

## Mandatory bootstrap

Before any Pulda work:

1. Read this file and `docs/governance/OPERATING-MODEL.md`.
2. Read the relevant CR, ADR/RFC, tests, schema/migrations, and implementation.
3. Read the corresponding Notion DNA and decisions through the authorized connection.
4. Check for a newer emergency patch and explicit user decision.
5. State a short baseline: confirmed, conflict, missing, assumption.
6. Do not implement when a material conflict or missing source can change the result.

Never infer current project state from chat memory alone.

## Authority

- Human: creator, messenger, actor, and final product authority.
- AI: disciple, watcher, and helper.
- Notion: approved operating DNA, meaning, decisions, and human corrections.
- Git: versioned specifications, code, tests, migrations, commits, and releases.
- Runtime: dated operational evidence.
- Builder: implements an approved unit and returns evidence.
- Emergency patch: temporary bridge that must be reconciled into Notion and Git.

## Change rules

- Capture new inputs as Events; infer hierarchy later.
- Update an existing canonical document before creating a duplicate.
- Use a CR for behavior changes and an ADR for durable architecture decisions.
- Keep user facts, AI interpretations, and revisions separate.
- Separate one-time exceptions from reusable corrections.
- Do not change the database, framework, authority model, privacy boundary, or core direction without explicit approval.
- Never commit real personal data, databases, attachments, backups, credentials, or secret configuration.
- Treat the ChatGPT GitHub integration as a read-only verification path unless the user explicitly changes this decision.
- Prepare Git changes as complete replacement files whenever safe; never place patch instructions at a canonical file path.
- When a full overwrite risks losing unrelated content, provide an exact VS Code target file, anchor text, and replacement region instead.
- The user reviews, commits, and pushes through GitHub Desktop; afterward the AI re-reads the remote commit and affected files.

## Minimum model rule

A Pulda minimum model must execute one complete cycle:

Event input → DB original preservation → AI interpretation → human correction/decision → action → result → AI follow-up → next Event/interpretation → reusable correction affects the next comparable interpretation.

A storage-only, classification-only, or UI-only prototype is not an MVP.

## Verification

A screenshot or plausible code is not implementation evidence. `Implemented` requires an approved source decision, CR acceptance criteria, a real commit, automated regression evidence, and reproducible execution. Data changes additionally require export/import and migration evidence.

Only the user may set `User Verified` or `Closed`.

## Completion report

Always report the baseline used, canonical objects and files changed, tests and Runtime evidence, reconciliation state, blockers, and the next smallest loop. Do not leave a material decision or implementation only in chat or a Builder workspace.
