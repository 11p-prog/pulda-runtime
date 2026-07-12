# UX-0001 Home

Status: Adopted for MVP redesign

## Purpose
Home lets the user capture reality, see recent activity, and review AI-generated context.

## Layout
1. Header
2. Event capture input
3. Activity Feed
4. AI Insight panel

## Event capture
- Placeholder: 무엇이 있었나요?
- Enter saves immediately.
- No mandatory category, project, goal, tag, or priority.
- Saved event appears at the top of the feed.

## Feed columns
- Captured time
- Event title
- Status
- Optional inferred context

## Time display
- Today: HH:mm
- Yesterday: 어제 HH:mm
- Within current year: MM-DD
- Older: YYYY-MM-DD

## Prohibited on Home
- Forced hierarchy selection
- Mandatory project assignment
- Goal creation flow
- Central Event/Task/Goal/Project tabs

## Acceptance criteria
- Event capture available immediately after Home load.
- One Enter action saves an event.
- Captured time is always visible.
- Feed sorts newest first.
- Home remains usable without understanding Pulda domain terms.
