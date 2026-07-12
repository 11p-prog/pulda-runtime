# UX-0002 Event Feed

## Purpose
Make accumulated events feel like a chronological record, not an unstructured storage table.

## Default presentation
- Newest first.
- Group by Today, Yesterday, Earlier this week, Earlier.
- Captured time always visible.
- Event title is primary text.
- Status is compact and secondary.

## Similar-event handling
Phase 1:
- Keep every event visible.
- Add inferred context label when confidence is high.

Phase 2:
- Offer collapsible clusters such as “Pulda Runtime activity (7)”.
- Never delete or overwrite source events.
- Cluster is a view, not a replacement record.

## Required fields
- id
- title
- captured_at
- status

## Optional fields
- occurred_at
- scheduled_at
- inferred_context_id
- source
