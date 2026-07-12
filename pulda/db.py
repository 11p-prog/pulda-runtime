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
CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  original_name TEXT NOT NULL,
  stored_name TEXT NOT NULL,
  mime_type TEXT,
  size_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspace_tabs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ctx TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  icon TEXT NOT NULL DEFAULT 'tab',
  removable INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0
);
"""

# CR-0011: workspace tabs became a user-managed list (Replit-style
# add/remove) instead of a hardcoded category set. "오늘" is seeded as the
# one permanent (non-removable) tab. The rest of this seed is a *draft
# sample*, inferred from the existing role vocabulary the app already
# classifies events into (see classifier.ROLE_KEYWORDS: 가족/회사/성당/개인)
# and from the CR-0002/0003 Church+Family tabs that already existed — not a
# new fixed category set. The user can remove/rearrange any of these; they
# exist only so the tab bar isn't empty on first migration.
DEFAULT_WORKSPACE_TABS = [
    ("today", "오늘", "target", 0, 0),
    ("role:성당", "Church", "church", 1, 10),
    ("role:가족", "Family", "diversity_3", 1, 20),
    ("role:회사", "Work", "work", 1, 30),
    ("role:개인", "Personal", "person", 1, 40),
    ("knowledge", "Knowledge", "school", 1, 50),
]

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

def _seed_workspace_tabs(conn: sqlite3.Connection) -> None:
    """Seed the draft tab set once, on first run only — after that the
    table is entirely user-managed (add/remove), so seeding must never
    re-insert a tab the user deliberately removed."""
    count = conn.execute("SELECT count(*) c FROM workspace_tabs").fetchone()[0]
    if count:
        return
    conn.executemany(
        "INSERT INTO workspace_tabs(ctx,label,icon,removable,sort_order) VALUES(?,?,?,?,?)",
        DEFAULT_WORKSPACE_TABS,
    )

def init_db() -> None:
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        _seed_workspace_tabs(conn)

@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
