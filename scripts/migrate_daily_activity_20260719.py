"""CR-0015 safe cleanup for the known 2026-07-19 mixed Daily Activity Event.

Dry-run is the default.  Apply only after retaining the JSON backup emitted by
this script.  2026-07-21 correction; recovery is documented in CR-0015.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pulda.db import init_db, connect
from pulda.timeutil import now_kst

DATE = "2026-07-19"
CHANNEL = "chatgpt"
TEST_KEY = "chatgpt:postgres-persistence-test:2026-07-19"
OPERATIONAL_KEY = "chatgpt:primary:2026-07-19"
TEST_SUMMARY = "Corrected Autoscale deployment started with PostgreSQL backend"

def snapshot():
    with connect() as conn:
        batch = conn.execute(
            "SELECT * FROM daily_activity_batches WHERE activity_date=? AND source_channel=?",
            (DATE, CHANNEL),
        ).fetchone()
        if not batch:
            raise SystemExit("No 2026-07-19 chatgpt Daily Activity batch found")
        event = conn.execute("SELECT * FROM events WHERE id=?", (batch["event_id"],)).fetchone()
        items = conn.execute(
            "SELECT * FROM daily_activity_items WHERE batch_id=? ORDER BY id", (batch["id"],)
        ).fetchall()
        receipts = conn.execute(
            "SELECT * FROM daily_activity_envelopes WHERE batch_id=? ORDER BY id", (batch["id"],)
        ).fetchall()
    return {"batch": dict(batch), "event": dict(event),
            "items": [dict(x) for x in items], "receipts": [dict(x) for x in receipts]}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", default="daily-activity-2026-07-19-backup.json")
    args = parser.parse_args()
    init_db()
    before = snapshot()
    Path(args.backup).write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
    test_items = [x for x in before["items"] if x["summary"] == TEST_SUMMARY]
    report = {"mode": "apply" if args.apply else "dry-run", "backup": args.backup,
              "event_id": before["event"]["id"], "item_count": len(before["items"]),
              "test_item_ids": [x["id"] for x in test_items]}
    if len(test_items) != 1:
        raise SystemExit(json.dumps({**report, "error": "expected exactly one known test item"}))
    if not args.apply:
        print(json.dumps(report, ensure_ascii=False))
        return
    now = now_kst().isoformat(timespec="seconds")
    with connect() as conn:
        batch = before["batch"]
        conn.execute(
            "UPDATE daily_activity_batches SET external_key=?, updated_at=? WHERE id=?",
            (f"{CHANNEL}:daily:{DATE}", now, batch["id"]),
        )
        cur = conn.execute(
            """INSERT INTO events(text,source,role,area,kind,urgency,importance,status,
            captured_at,occurred_on,project,created_at,updated_at)
            VALUES(?,?,'자아','시스템','event',1,1,'recorded',?,?,?, ?,?)""",
            (f"{DATE} Test ChatGPT Daily Activity", "daily_activity:chatgpt:test",
             now, DATE, "PRJ-PULDA-OS", now, now),
        )
        test_event_id = cur.lastrowid
        cur = conn.execute(
            """INSERT INTO daily_activity_batches
            (event_id,activity_date,source_channel,external_key,source_coverage,access_gaps,
             privacy_reviewed,status,created_at,updated_at)
            VALUES(?,?,?,?,'CR-0015/0016 persistence verification','',1,'registered',?,?)""",
            (test_event_id, DATE, "chatgpt:test", f"chatgpt:test:daily:{DATE}", now, now),
        )
        test_batch_id = cur.lastrowid
        conn.execute("UPDATE daily_activity_items SET batch_id=? WHERE id=?",
                     (test_batch_id, test_items[0]["id"]))
        empty_hash = "migration-2026-07-21-known-envelope"
        for target_batch, key, klass, count in (
            (test_batch_id, TEST_KEY, "test", 1),
            (batch["id"], OPERATIONAL_KEY, "operational", len(before["items"]) - 1),
        ):
            conn.execute(
                """INSERT OR IGNORE INTO daily_activity_envelopes
                (batch_id,external_key,data_class,payload_hash,added_count,status,processed_at)
                VALUES(?,?,?,?,?,'processed',?)""",
                (target_batch, key, klass, empty_hash, count, now),
            )
    after = snapshot()
    print(json.dumps({**report, "operational_item_count": len(after["items"]),
                      "test_event_id": test_event_id, "test_batch_id": test_batch_id},
                     ensure_ascii=False))

if __name__ == "__main__":
    main()
