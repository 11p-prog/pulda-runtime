# Pulda Privacy Architecture

Status: living document. Written in response to Review v3 #5 ("Privacy-first
Architecture") and #7 ("Local AI Preparation"). Privacy is treated as a
product requirement, not an optional feature, because Pulda's data model is
explicitly designed to eventually hold: family, finance, medical, work,
decisions, journals, credentials, and long-term personal history.

## Principles (from Review v3 #5)

1. **Local-first where practical** — SQLite on disk (`data/pulda.db`) is the
   source of truth today; no data leaves the repl unless a sync/AI feature
   explicitly sends it.
2. **Explicit user control over AI providers** — no feature should silently
   route sensitive text to a cloud AI provider the user didn't choose.
3. **AI access is permission-based** — a feature that wants to send Event
   data to an external AI provider must be opt-in per data class, not a
   blanket "AI is on" toggle.
4. **Sensitive data is classified before external transmission** — every
   Event already carries `role`/`area` (가족/재무/건강/성당/회사/개인, etc.);
   this classification should gate what's allowed to leave the system, not
   just how it's displayed.
5. **Provider independence** — no feature should hard-depend on one AI
   vendor's API shape; classification/extraction logic should be swappable.
6. **Future support for local LLMs** — the architecture should not assume an
   always-available internet connection to a cloud model.
7. **Encryption for stored sensitive information** — fields carrying
   finance/medical/credential-like content should be encryptable at rest,
   not just access-controlled by the OS/filesystem.
8. **Exportability without vendor lock-in** — the user must always be able
   to get their own data out in a plain, non-proprietary format.

## Current state (as of this MVP)

- **Storage**: SQLite, file-based, local to the repl (`data/pulda.db`,
  gitignored). Not encrypted at rest yet — principle #7 is not yet met.
- **Classification**: `pulda/classifier.py` is a deterministic keyword-based
  classifier (no LLM call, no external request) — this already satisfies
  "local-first" and "provider independence" for the core capture path.
- **External data flows** (the only paths where Event data currently leaves
  the local system):
  - Notion sync (`pulda/connectors.py::sync_notion`) — sends daily review
    summaries to a Notion page via the Replit-managed Notion connector.
    Opt-in via `AUTO_SYNC_NOTION`.
  - GitHub sync (`sync_github`) — currently off by default
    (`AUTO_SYNC_GITHUB`), used for code/repo sync, not Event content.
  - Neither path currently checks an Event's `role`/`area` classification
    before sending it — this is a gap against principle #4 (see below).
- **No cloud LLM calls exist yet** in the current codebase — `classifier.py`
  and `service.py`'s "Decision Support" insights are both rule-based, not
  model-based. This means principles #2/#3/#6 have nothing to violate yet,
  but also nothing enforcing them once an AI feature is added.

## Gaps and required guardrails for future work

These are constraints future features must satisfy — not yet-built
features themselves:

- **Before any feature sends Event text to an external AI provider**, it
  must check the Event's `role`/`area` against a configurable sensitivity
  list (e.g. 재무/건강/가족 flagged sensitive by default) and either skip,
  redact, or require explicit per-event/per-session consent for flagged
  data. This is the concrete mechanism for principle #4.
- **Any new AI-provider integration** (OpenAI, Anthropic, etc., via Replit
  connectors or otherwise) must be wired behind a single provider-selection
  setting, not called directly from feature code — so swapping or disabling
  the provider doesn't require touching every call site (principles #2/#3/#5).
- **Historical import** (Review v3 #4, Google Docs journals) is the highest-
  risk future feature from a privacy standpoint: it's a bulk bring-in of
  potentially years of personal journal content. Any AI classification step
  in that pipeline must run through the same sensitivity gate above, and the
  raw imported text should be retained locally (not only the AI's
  structured output) so nothing is silently one-way-transformed through a
  cloud call.
- **Encryption at rest (principle #7)** is not implemented. If/when
  finance/medical/credential fields are added as first-class columns
  (beyond the current free-text `text`/`financial_impact`/`family_impact`),
  those columns should be encrypted with a key not stored in the same SQLite
  file — e.g. via `cryptography`'s Fernet with a key from Replit Secrets.
- **Export (principle #8)**: `GET /api/events` already returns full event
  data as JSON, which is a workable start toward exportability. A dedicated
  "export everything" endpoint (all tables, not just events) should be
  added before any feature that increases lock-in risk (e.g. a proprietary
  sync format).

## Local AI preparation (Review v3 #7)

No local LLM is wired up yet, and Replit's environment does not provide a
GPU-backed local inference runtime out of the box, so "local LLM support" is
prepared for, not implemented, in this iteration:

- Keep classification logic (`classifier.py`) rule-based and provider-free
  for as long as possible — it already works without any LLM and should
  remain the fallback path even after an AI provider is introduced.
- When an AI provider is introduced (cloud or local), route all calls
  through one module (e.g. `pulda/ai_provider.py`, not yet created) with a
  provider-agnostic interface (`classify_with_ai(text) -> Classification`),
  so a future local-LLM backend (e.g. via Ollama or a Replit-hosted model)
  is a drop-in provider, not a rewrite.
- Do not persist raw prompts/responses from any future cloud AI call
  alongside sensitive Event fields without the same sensitivity gate
  described above.

## Data ownership and portability contract

Applications and Builders are replaceable. Human Events, corrections, outcomes, provenance, and revision history are not.

### Separation

- Git may contain code, empty schema, migrations, tests, synthetic fixtures, and reviewed documentation.
- Real Events, people, family, finance, parish, client data, databases, attachments, exports, backups, credentials, and secret configuration must never enter the public Git repository.
- AI interpretations must remain distinguishable from user facts.
- Reusable human corrections belong in approved DNA/rules with a Runtime version reference; one-time exceptions remain Event-level revisions.
- Backups and exports belong in encrypted or otherwise private user-controlled storage.

### Required round trip

Before real-use expansion, Runtime must provide and verify:

1. a full structured export with schema/app version and timestamps
2. an attachment manifest and integrity checks
3. import into an empty environment without overwriting the source
4. record-count, stable-ID, relationship, revision, and attachment comparison
5. documented migration and rollback
6. a platform-independent Builder handoff

SQLite remains acceptable during MVP. Replacing storage requires an approved ADR and a verified round-trip migration.

No data feature is `Implemented` without reproducible export/import evidence and confirmation that a connector failure does not lose the Runtime Event.

Updated: 2026-07-14
