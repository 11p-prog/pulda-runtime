# Pulda Runtime Help

This is the living user-facing guide for behavior that exists in the current
Runtime. Update it in the same Git change whenever visible behavior or a user
constraint changes.

## Capture an Event

- Enter natural language in the bottom capture bar. Pulda stores the original
  text first and infers role, area, kind, urgency, and importance afterward.
- One capture currently creates one Event. Multi-Event splitting, candidate
  review, merge, exclusion, and approval are planned but not implemented.
- Attachments currently accept PDF and common image formats up to the configured
  size limit (20 MB by default). The file is stored as evidence; text extraction
  and Event-candidate generation are not implemented yet.

## Run the first Living Loop by API

The current UI does not expose interpretation and correction controls yet. A
reproducible backend loop is available through these endpoints:

1. `POST /api/events` — preserve the original Event.
2. `POST /api/events/{event_id}/interpretations` — create a versioned
   interpretation with model, prompt, DNA version, confidence, and source
   evidence.
3. `POST /api/interpretations/{interpretation_id}/corrections` — store a human
   correction. Use `scope: one_time` for an exception or `scope: reusable` with
   `reusable_match_text` to create a rule for comparable Events.
4. `POST /api/events/{event_id}/outcomes` — record the real result.
5. `POST /api/events/{event_id}/follow-ups` — create a follow-up proposal tied
   to that outcome.
6. Create and interpret a comparable Event. Its `applied_rule_ids` shows whether
   the reusable correction affected the next interpretation.

This is backend execution evidence, not user verification. The classifier is
still rule-based and there is no live LLM provider or human-review UI.

## Change and delete records

- Normal delete is a soft delete: the Event disappears from active lists but
  remains stored and a deletion transition appears in history.
- Hard delete permanently purges an accidental duplicate and its attachment and
  status history. Use it only when no record should remain.
- Restore-window controls, Event binding/unbinding, history filters, and copying
  an old record into a new Event are planned but not implemented.

## First-use guidance rule

Essential concepts such as original preservation, one-time versus reusable
correction, soft versus hard delete, and approval before multi-Event creation
must be taught inline through a tooltip or short guide when their UI is added.
The Help page remains the detailed reference.
