import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'manual',
  role TEXT NOT NULL,
  area TEXT NOT NULL,
  kind TEXT NOT NULL,
  urgency INTEGER NOT NULL,
  importance INTEGER NOT NULL,
  status TEXT NOT NULL,
  scheduled_at TEXT,
  due_date TEXT,
  project TEXT,
  goal TEXT,
  financial_impact TEXT,
  family_impact TEXT,
  blocked_by TEXT,
  defer_reason TEXT,
  next_review_at TEXT,
  notion_page_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_date TEXT NOT NULL UNIQUE,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL,
  target TEXT,
  status TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  event_text TEXT NOT NULL,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  changed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  original_name TEXT NOT NULL,
  stored_name TEXT NOT NULL,
  mime_type TEXT,
  size_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
"""

NEW_EVENT_COLUMNS = {
    "project": "TEXT",
    "goal": "TEXT",
    "financial_impact": "TEXT",
    "family_impact": "TEXT",
    "blocked_by": "TEXT",
    "defer_reason": "TEXT",
    "next_review_at": "TEXT",
    "notion_page_id": "TEXT",
}

def _migrate(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    for column, col_type in NEW_EVENT_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE events ADD COLUMN {column} {col_type}")
    review_columns = {row[1] for row in conn.execute("PRAGMA table_info(reviews)").fetchall()}
    if "reflection" not in review_columns:
        conn.execute("ALTER TABLE reviews ADD COLUMN reflection TEXT")
    # CR-0011 (user-managed tab bar) was reverted per CR-0012/IA-0001 (single
    # Activity Feed + fixed nav, decided 2026-07-13) — drop the now-unused
    # table on any DB that already created it.
    conn.execute("DROP TABLE IF EXISTS workspace_tabs")

def init_db() -> None:
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)

@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
