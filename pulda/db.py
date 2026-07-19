import sqlite3
import re
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
CREATE TABLE IF NOT EXISTS event_interpretations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  revision_no INTEGER NOT NULL,
  summary TEXT NOT NULL,
  role TEXT NOT NULL,
  area TEXT NOT NULL,
  kind TEXT NOT NULL,
  urgency INTEGER NOT NULL,
  importance INTEGER NOT NULL,
  confidence REAL NOT NULL,
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  dna_version TEXT NOT NULL,
  source_evidence TEXT NOT NULL,
  applied_rule_ids TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  UNIQUE(event_id, revision_no)
);
CREATE TABLE IF NOT EXISTS correction_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  match_text TEXT NOT NULL,
  target_field TEXT NOT NULL,
  target_value TEXT NOT NULL,
  rationale TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  interpretation_id INTEGER NOT NULL REFERENCES event_interpretations(id),
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT NOT NULL,
  scope TEXT NOT NULL CHECK(scope IN ('one_time','reusable')),
  rationale TEXT NOT NULL,
  rule_id INTEGER REFERENCES correction_rules(id),
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  result_text TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS follow_up_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL REFERENCES events(id),
  outcome_id INTEGER NOT NULL REFERENCES event_outcomes(id),
  text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL UNIQUE REFERENCES events(id),
  source_type TEXT NOT NULL,
  canonical_url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  publisher TEXT,
  published_at TEXT,
  storage_uri TEXT NOT NULL,
  storage_format TEXT NOT NULL,
  archival_status TEXT NOT NULL,
  summary TEXT NOT NULL,
  relevance_note TEXT NOT NULL,
  tags_json TEXT NOT NULL DEFAULT '[]',
  related_contexts_json TEXT NOT NULL DEFAULT '[]',
  content_hash TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_activity_batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL UNIQUE REFERENCES events(id),
  activity_date TEXT NOT NULL,
  source_channel TEXT NOT NULL,
  external_key TEXT NOT NULL UNIQUE,
  source_coverage TEXT NOT NULL DEFAULT '',
  access_gaps TEXT NOT NULL DEFAULT '',
  privacy_reviewed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'registered',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(activity_date, source_channel)
);
CREATE TABLE IF NOT EXISTS daily_activity_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id INTEGER NOT NULL REFERENCES daily_activity_batches(id),
  item_key TEXT NOT NULL,
  item_type TEXT NOT NULL CHECK(item_type IN ('instruction','decision','work_result','action_candidate','hold')),
  project TEXT,
  summary TEXT NOT NULL,
  source_ref TEXT,
  review_state TEXT NOT NULL DEFAULT 'register' CHECK(review_state IN ('register','record_only','exclude','review_needed')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(batch_id, item_key)
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
    "deleted_at": "TEXT",
}

# Resolved at startup — True only when DATABASE_URL is set AND reachable.
_postgres_available: bool = False

def database_backend() -> str:
    return "postgresql" if _postgres_available else "sqlite"

def _migrate_sqlite(conn: sqlite3.Connection) -> None:
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
    global _postgres_available
    if settings.database_url:
        try:
            _init_postgres()
            _postgres_available = True
            return
        except Exception as exc:
            import logging
            logging.warning(
                "PostgreSQL unreachable at startup (%s) — falling back to SQLite. "
                "Switch to Reserved VM deployment for persistent PostgreSQL access.", exc
            )
            _postgres_available = False
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate_sqlite(conn)

def _postgres_schema() -> str:
    schema = SCHEMA.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
    schema = re.sub(r"\b(INTEGER)(\s+(?:NOT NULL\s+)?REFERENCES)", r"BIGINT\2", schema)
    return schema

def _init_postgres() -> None:
    import psycopg
    with psycopg.connect(settings.database_url) as conn:
        # Autoscale can start multiple instances together. Serialize schema
        # initialization inside PostgreSQL so concurrent boots cannot race.
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('pulda_runtime_schema_v1'))")
        for statement in _postgres_schema().split(";"):
            if statement.strip():
                conn.execute(statement)
        for column, col_type in NEW_EVENT_COLUMNS.items():
            conn.execute(f"ALTER TABLE events ADD COLUMN IF NOT EXISTS {column} {col_type}")
        conn.execute("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS reflection TEXT")
        conn.execute("DROP TABLE IF EXISTS workspace_tabs")

def _postgres_sql(sql: str) -> str:
    converted = sql.replace("?", "%s")
    if re.match(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\b", converted, re.IGNORECASE):
        converted = re.sub(
            r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", converted,
            count=1, flags=re.IGNORECASE,
        ).rstrip() + " ON CONFLICT DO NOTHING"
    return converted

class _PostgresCursor:
    def __init__(self, cursor, lastrowid=None, rowcount=None):
        self._cursor = cursor
        self.lastrowid = lastrowid
        self.rowcount = cursor.rowcount if rowcount is None else rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

class _PostgresConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql: str, params=()):
        converted = _postgres_sql(sql)
        is_insert = bool(re.match(r"^\s*INSERT\b", converted, re.IGNORECASE))
        if is_insert and "RETURNING" not in converted.upper():
            converted = converted.rstrip() + " RETURNING id"
            cursor = self._connection.execute(converted, params)
            rowcount = cursor.rowcount
            row = cursor.fetchone()
            lastrowid = row["id"] if row else None
            return _PostgresCursor(cursor, lastrowid=lastrowid, rowcount=rowcount)
        return _PostgresCursor(self._connection.execute(converted, params))

@contextmanager
def connect():
    if _postgres_available:
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect(settings.database_url, row_factory=dict_row)
        try:
            yield _PostgresConnection(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
