# Pulda Runtime MVP

Korean-language personal productivity app. Captures free-text events, auto-classifies them into tasks, and displays a daily activity feed.

## Stack

- **Backend**: FastAPI + Uvicorn (Python 3.11)
- **Storage**: SQLite (`data/pulda.db`)
- **Templates**: Jinja2 (in `pulda/templates/`)
- **Scheduler**: APScheduler (daily review at 22:30 KST)

## How to run

The workflow `Start application` runs `python -m pulda.app` and serves on port 5000.

Key env vars (set in Replit environment):
- `PULDA_PORT=5000` — port to listen on (required for Replit webview)
- `PULDA_HOST=0.0.0.0` — bind to all interfaces

## Optional integrations (off by default)

Set `AUTO_SYNC_NOTION=true` and provide `NOTION_TOKEN` + `NOTION_PARENT_PAGE_ID` to enable Notion sync.  
Set `AUTO_SYNC_GITHUB=true` and provide `GITHUB_TOKEN` + `GITHUB_REPOSITORY` to enable GitHub sync.

## Project structure

```
pulda/
  app.py          # FastAPI routes
  service.py      # Business logic
  db.py           # SQLite schema & queries
  classifier.py   # Rule-based event classifier
  connectors.py   # Notion & GitHub sync
  scheduler.py    # APScheduler daily review job
  config.py       # Settings from env vars
  templates/      # Jinja2 HTML templates
data/             # SQLite DB and attachments (auto-created)
docs/             # ADRs, RFCs, UX specs, change requests
```

## User preferences

- Keep Korean UI text as-is
- Do not restructure the existing module layout
