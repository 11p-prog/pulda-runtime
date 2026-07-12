# Historical Import Pipeline (Phase 2 design — not yet implemented)

Status: design placeholder only. Nothing in this document is built yet.
Captured now so Phase 2 starts from a provider-independent architecture
instead of a Google-Docs-shaped one-off, per explicit user direction.

## Why "pipeline", not "Google Docs import"

The user's first source is Google Docs journals, but the requirement is a
general **historical import pipeline** that Google Docs is only the first
provider for. Building it as a Google-Docs-specific feature would make
every later source (Markdown, Notion Export, TXT, PDF, and whatever comes
after) a bolt-on special case instead of a natural second provider.

## Pipeline shape

```
Source (provider-specific)  →  Raw Text Extraction  →  Timeline Reconstruction
   →  Classification (rule-based classifier, per user's Phase-1 decision)
   →  Role / Project / Family / Business linking  →  Searchable Event History
```

- **Source / Raw Text Extraction** is the only provider-specific layer.
  Each source (Google Docs, Markdown, Notion Export, TXT, PDF, future) is a
  small adapter that implements one interface — something like
  `extract(source_ref) -> list[RawDocument]`, where `RawDocument` is just
  `{text, source_type, source_ref, original_date_hint}`. No downstream stage
  should need to know which provider a `RawDocument` came from.
- **Timeline Reconstruction** turns each `RawDocument` into one or more
  dated fragments (a journal entry often covers a whole day of a period;
  the pipeline needs to infer/assign real dates so imported Events land on
  the correct day in the workspace's date axis — see the Date Workspace
  Activation work already shipped).
- **Classification** reuses the existing rule-based `classifier.py` — per
  the user's Phase-1 decision, historical import should NOT call an external
  AI provider for extraction/classification. If that changes later, the
  privacy gate described in `docs/PRIVACY_ARCHITECTURE.md` (sensitivity
  check before any external AI call) applies to this pipeline too.
- **Role/Project/Family/Business linking** produces the same `events` rows
  the rest of the app already uses (`create_event`), tagged with
  `source="import:<provider>"` so imported history stays distinguishable
  from live captures and can be re-run/audited per source.
- **Searchable Event History** is just the existing `events` table plus
  whatever search feature is added on top later — no new storage model
  needed, since imported entries become ordinary Events.

## Provider adapter contract (for when this is built)

Each provider adapter should be a small, isolated module implementing:

- `list_sources() -> list[SourceRef]` — enumerate what's importable (e.g.
  Google Docs: list of doc IDs/titles; folder of Markdown files: file
  paths; Notion Export: pages in a zip; PDF/TXT: uploaded files).
- `extract(source_ref) -> list[RawDocument]` — pull raw text + a best-effort
  date hint, nothing else. No classification, no Event creation here.

Everything after `extract()` is provider-agnostic and shared. This keeps
adding a new source (e.g. "future sources") to a single new adapter file,
not a change to the timeline/classification/linking stages.

## Known unresolved design questions for Phase 2 kickoff

- Where does "list of importable sources" come from for Google Docs
  specifically — does it need the Google integration (OAuth), or does the
  user manually paste/export first? (Deferred — no decision made yet.)
- How are duplicate imports (re-running the same source) detected and
  handled — some idempotency key derived from `(source_type, source_ref,
  fragment offset)` is likely needed before this ships.
- UI for reviewing/correcting imported Events before they're treated as
  first-class history (bulk import will produce noisier classification
  results than live single-line capture).

None of the above needs to be answered before Phase 1 (this iteration) is
considered complete — they're scoped here only so Phase 2 doesn't have to
re-derive the shape from scratch.
