"""Repair the missing CR-0015 receipt for the 2026-07-22 Daily Activity.

Dry-run is the default. The script always writes a private JSON backup under
data/backups before --apply. It reads the canonical Notion envelope and lets the
normal idempotent capture service add only a missing receipt or missing items.
"""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pulda.connectors import _block_plain_text, _notion_request
from pulda.db import connect, init_db
from pulda.service import capture_daily_activity

DATE = "2026-07-22"
CHANNEL = "chatgpt"
EXTERNAL_KEY = "chatgpt:primary:2026-07-22"
DEFAULT_BACKUP = "data/backups/daily-activity-2026-07-22-before-repair.json"


def snapshot() -> dict:
    with connect() as conn:
        batch = conn.execute(
            "SELECT * FROM daily_activity_batches WHERE activity_date=? AND source_channel=?",
            (DATE, CHANNEL),
        ).fetchone()
        if not batch:
            raise SystemExit("No 2026-07-22 chatgpt Daily Activity batch found")
        event = conn.execute(
            "SELECT * FROM events WHERE id=?", (batch["event_id"],)
        ).fetchone()
        items = conn.execute(
            "SELECT * FROM daily_activity_items WHERE batch_id=? ORDER BY id",
            (batch["id"],),
        ).fetchall()
        receipts = conn.execute(
            "SELECT * FROM daily_activity_envelopes WHERE batch_id=? ORDER BY id",
            (batch["id"],),
        ).fetchall()
    return {
        "batch": dict(batch),
        "event": dict(event),
        "items": [dict(row) for row in items],
        "receipts": [dict(row) for row in receipts],
    }


def write_backup(path: str, data: dict) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def find_queue_envelope() -> tuple[dict, str]:
    from pulda.config import settings

    page_id = settings.notion_daily_activity_queue_page_id
    if not page_id:
        raise SystemExit("NOTION_DAILY_ACTIVITY_QUEUE_PAGE_ID missing")
    matches: list[tuple[dict, str]] = []
    cursor = None
    while True:
        suffix = "?page_size=100"
        if cursor:
            suffix += f"&start_cursor={quote(cursor)}"
        response = _notion_request("GET", f"/v1/blocks/{page_id}/children{suffix}")
        response.raise_for_status()
        body = response.json()
        for block in body.get("results", []):
            raw = _block_plain_text(block)
            if not raw.startswith("{"):
                continue
            try:
                envelope = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if (
                envelope.get("kind") == "pulda-daily-activity"
                and envelope.get("external_key") == EXTERNAL_KEY
            ):
                matches.append((envelope, block.get("id")))
        if not body.get("has_more"):
            break
        cursor = body.get("next_cursor")
        if not cursor:
            raise SystemExit("Notion pagination reported has_more without next_cursor")
    if len(matches) != 1:
        raise SystemExit(
            json.dumps(
                {"error": "expected exactly one canonical queue envelope", "matches": len(matches)}
            )
        )
    return matches[0]


def restore(backup_path: str) -> dict:
    before = json.loads(Path(backup_path).read_text(encoding="utf-8"))
    current = snapshot()
    if (
        current["batch"]["id"] != before["batch"]["id"]
        or current["event"]["id"] != before["event"]["id"]
    ):
        raise SystemExit("Backup does not match the current 2026-07-22 Event and batch")

    recovery_copy = write_backup(
        "data/backups/daily-activity-2026-07-22-before-restore.json", current
    )
    batch_id = before["batch"]["id"]
    with connect() as conn:
        conn.execute("DELETE FROM daily_activity_envelopes WHERE batch_id=?", (batch_id,))
        for row in before["receipts"]:
            conn.execute(
                """INSERT INTO daily_activity_envelopes
                (id,batch_id,external_key,data_class,source_block_id,payload_hash,
                 added_count,status,error,processed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["id"], row["batch_id"], row["external_key"], row["data_class"],
                    row.get("source_block_id"), row["payload_hash"], row["added_count"],
                    row["status"], row.get("error"), row["processed_at"],
                ),
            )
        conn.execute("DELETE FROM daily_activity_items WHERE batch_id=?", (batch_id,))
        for row in before["items"]:
            conn.execute(
                """INSERT INTO daily_activity_items
                (id,batch_id,item_key,item_type,project,summary,source_ref,review_state,
                 created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["id"], row["batch_id"], row["item_key"], row["item_type"],
                    row.get("project"), row["summary"], row.get("source_ref"),
                    row["review_state"], row["created_at"], row["updated_at"],
                ),
            )
        batch = before["batch"]
        conn.execute(
            """UPDATE daily_activity_batches
            SET external_key=?,source_coverage=?,access_gaps=?,privacy_reviewed=?,
                status=?,created_at=?,updated_at=? WHERE id=?""",
            (
                batch["external_key"], batch["source_coverage"], batch["access_gaps"],
                batch["privacy_reviewed"], batch["status"], batch["created_at"],
                batch["updated_at"], batch_id,
            ),
        )
        conn.execute(
            "UPDATE events SET updated_at=? WHERE id=?",
            (before["event"]["updated_at"], before["event"]["id"]),
        )
    return {
        "status": "restored",
        "backup": backup_path,
        "pre_restore_backup": str(recovery_copy),
        "event_id": before["event"]["id"],
        "item_count": len(before["items"]),
        "receipt_count": len(before["receipts"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--restore")
    parser.add_argument("--backup", default=DEFAULT_BACKUP)
    args = parser.parse_args()

    init_db()
    if args.restore:
        print(json.dumps(restore(args.restore), ensure_ascii=False))
        return

    before = snapshot()
    backup = write_backup(args.backup, before)
    existing = [
        row for row in before["receipts"] if row["external_key"] == EXTERNAL_KEY
    ]
    if len(existing) == 1:
        print(
            json.dumps(
                {
                    "mode": "apply" if args.apply else "dry-run",
                    "status": "already_repaired",
                    "backup": str(backup),
                    "event_id": before["event"]["id"],
                    "item_count": len(before["items"]),
                    "receipt_count": 1,
                },
                ensure_ascii=False,
            )
        )
        return
    if len(existing) > 1:
        raise SystemExit("Duplicate 2026-07-22 external_key receipts already exist")

    envelope, block_id = find_queue_envelope()
    report = {
        "mode": "apply" if args.apply else "dry-run",
        "backup": str(backup),
        "event_id": before["event"]["id"],
        "batch_id": before["batch"]["id"],
        "item_count_before": len(before["items"]),
        "receipt_count_before": len(before["receipts"]),
        "external_key": EXTERNAL_KEY,
        "source_block_id": block_id,
    }
    if not args.apply:
        print(json.dumps(report, ensure_ascii=False))
        return

    payload = {
        key: envelope.get(key)
        for key in (
            "activity_date", "source_channel", "external_key", "source_coverage",
            "access_gaps", "privacy_reviewed", "items", "data_class",
        )
    }
    payload["data_class"] = payload.get("data_class") or "operational"
    payload["source_block_id"] = block_id
    result = capture_daily_activity(**payload)
    after = snapshot()
    repaired = [
        row for row in after["receipts"] if row["external_key"] == EXTERNAL_KEY
    ]
    if result["event"]["id"] != before["event"]["id"] or len(repaired) != 1:
        raise SystemExit(json.dumps({**report, "status": "verification_failed"}))
    print(
        json.dumps(
            {
                **report,
                "status": "repaired",
                "event_id": result["event"]["id"],
                "added_count": result["added_count"],
                "item_count_after": len(after["items"]),
                "receipt_count_after": len(after["receipts"]),
                "duplicate_prevented": len(repaired) == 1,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
