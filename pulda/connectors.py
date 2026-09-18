import base64
import json
import requests
from .config import settings
from .service import audit, latest_review, capture_daily_activity, create_event, update_status
from .connector_client import connector_proxy, is_connector_available

def check_notion() -> dict:
    """Verify the Notion connection and configured target page, per
    PROJECT_REGISTRY.md's startup validation rule: confirm identity and
    that the configured page is reachable before allowing writes."""
    use_connector = is_connector_available()
    page_id = settings.notion_sync_page_id

    if not use_connector and not settings.notion_token:
        return {"ok": False, "connected": False, "error": "Notion not connected: set up the Notion connector or NOTION_TOKEN"}

    try:
        if use_connector:
            me = connector_proxy("notion", "/v1/users/me")
        else:
            me = requests.get(
                "https://api.notion.com/v1/users/me",
                headers={"Authorization": f"Bearer {settings.notion_token}", "Notion-Version": "2022-06-28"},
                timeout=20,
            )
        me.raise_for_status()
        me_json = me.json()
        bot_owner = (me_json.get("bot") or {}).get("owner", {})
        person = bot_owner.get("user", {}).get("person", {}) if bot_owner.get("type") == "user" else {}
        identity = {
            "workspace_name": (me_json.get("bot") or {}).get("workspace_name"),
            "account_email": person.get("email"),
        }
    except Exception as e:
        audit("check_notion", page_id, "failed", str(e))
        return {"ok": False, "connected": False, "error": str(e)}

    if not page_id:
        return {"ok": False, "connected": True, "identity": identity, "error": "NOTION_SYNC_PAGE_ID missing"}

    try:
        if use_connector:
            page = connector_proxy("notion", f"/v1/blocks/{page_id}")
        else:
            page = requests.get(
                f"https://api.notion.com/v1/blocks/{page_id}",
                headers={"Authorization": f"Bearer {settings.notion_token}", "Notion-Version": "2022-06-28"},
                timeout=20,
            )
        page.raise_for_status()
    except Exception as e:
        audit("check_notion", page_id, "failed", f"target page unreachable: {e}")
        return {"ok": False, "connected": True, "identity": identity, "target_page_id": page_id,
                "error": f"target page unreachable: {e}"}

    audit("check_notion", page_id, "success", identity.get("account_email") or "")
    return {"ok": True, "connected": True, "identity": identity, "target_page_id": page_id}

def sync_notion() -> dict:
    review = latest_review()
    if not review:
        return {"ok": False, "error": "no review"}
    page_id = settings.notion_sync_page_id
    if not page_id:
        return {"ok": False, "error": "NOTION_SYNC_PAGE_ID missing"}

    text = review["summary"][:1900]
    payload = {"children": [{
        "object": "block", "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }]}

    # Prefer the Replit-managed Notion connector (no token to manage/rotate).
    # Falls back to a manually-configured NOTION_TOKEN for portability outside Replit.
    use_connector = is_connector_available()
    if not use_connector and not settings.notion_token:
        return {"ok": False, "error": "Notion not connected: set up the Notion connector or NOTION_TOKEN"}

    try:
        if use_connector:
            r = connector_proxy("notion", f"/v1/blocks/{page_id}/children", method="PATCH", json_body=payload)
        else:
            r = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers={
                    "Authorization": f"Bearer {settings.notion_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                json=payload, timeout=20,
            )
        r.raise_for_status()
        audit("sync_notion", page_id, "success", review["review_date"])
        return {"ok": True}
    except Exception as e:
        audit("sync_notion", page_id, "failed", str(e))
        return {"ok": False, "error": str(e)}

def _notion_request(method: str, path: str, json_body: dict | None = None):
    use_connector = is_connector_available()
    if use_connector:
        return connector_proxy("notion", path, method=method, json_body=json_body)
    if not settings.notion_token:
        raise RuntimeError("Notion not connected: set up the Notion connector or NOTION_TOKEN")
    return requests.request(
        method,
        f"https://api.notion.com{path}",
        headers={
            "Authorization": f"Bearer {settings.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        json=json_body,
        timeout=20,
    )

def _block_plain_text(block: dict) -> str:
    block_type = block.get("type", "")
    rich_text = (block.get(block_type) or {}).get("rich_text", [])
    return "".join(part.get("plain_text", "") for part in rich_text).strip()

def pull_notion_daily_activities() -> dict:
    """Register privacy-reviewed envelopes from the canonical Notion queue.

    Queue blocks stay append-only. Runtime external keys and item hashes make
    retries safe and provide acknowledgement through the returned Event ID.
    """
    page_id = settings.notion_daily_activity_queue_page_id
    if not page_id:
        return {"ok": False, "error": "NOTION_DAILY_ACTIVITY_QUEUE_PAGE_ID missing"}

    processed = []
    ignored = 0
    checkpoint_key = f"notion-daily-activity:{page_id}"
    from .db import connect
    with connect() as conn:
        checkpoint = conn.execute(
            "SELECT cursor FROM connector_checkpoints WHERE connector_key=?", (checkpoint_key,)
        ).fetchone()
    cursor = checkpoint["cursor"] if checkpoint else None
    last_block_id = None
    try:
        while True:
            suffix = "?page_size=100"
            if cursor:
                from urllib.parse import quote
                suffix += f"&start_cursor={quote(cursor)}"
            response = _notion_request("GET", f"/v1/blocks/{page_id}/children{suffix}")
            response.raise_for_status()
            body = response.json()
            for block in body.get("results", []):
                last_block_id = block.get("id") or last_block_id
                raw = _block_plain_text(block)
                if not raw.startswith("{"):
                    continue
                try:
                    envelope = json.loads(raw)
                except json.JSONDecodeError:
                    ignored += 1
                    continue
                if envelope.get("kind") != "pulda-daily-activity":
                    continue
                payload = {key: envelope.get(key) for key in (
                    "activity_date", "source_channel", "external_key",
                    "source_coverage", "access_gaps", "privacy_reviewed", "items", "data_class",
                )}
                payload["data_class"] = payload.get("data_class") or "operational"
                payload["source_block_id"] = block.get("id")
                result = capture_daily_activity(**payload)
                processed.append({
                    "external_key": payload["external_key"],
                    "event_id": result["event"]["id"],
                    "batch_id": result["batch"]["id"],
                    "created": result["created"],
                    "added_count": result["added_count"],
                })
            if not body.get("has_more"):
                break
            cursor = body.get("next_cursor")

        if last_block_id:
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            with connect() as conn:
                conn.execute(
                    """INSERT INTO connector_checkpoints(connector_key,cursor,updated_at)
                    VALUES(?,?,?) ON CONFLICT(connector_key) DO UPDATE
                    SET cursor=excluded.cursor, updated_at=excluded.updated_at""",
                    (checkpoint_key, last_block_id, now),
                )

        audit("pull_notion_daily_activities", page_id, "success", f"processed={len(processed)}")
        return {"ok": True, "processed": processed, "ignored": ignored,
                "checkpoint": last_block_id or (checkpoint["cursor"] if checkpoint else None),
                "event_ids": sorted({row["event_id"] for row in processed}),
                "added_count": sum(row["added_count"] for row in processed), "errors": []}
    except Exception as e:
        audit("pull_notion_daily_activities", page_id, "failed", str(e))
        return {"ok": False, "processed": processed, "ignored": ignored,
                "checkpoint": checkpoint["cursor"] if checkpoint else None,
                "event_ids": sorted({row["event_id"] for row in processed}),
                "added_count": sum(row["added_count"] for row in processed),
                "errors": [{"error": str(e)}], "error": str(e)}

# Property/status-option ids for the property-based Notion "daily log"
# database (distinct from the JSON-envelope queue above). Notion keeps these
# ids stable across column renames, so matching by id survives the source DB
# being restyled -- only a deleted/recreated property or status option would
# require updating them.
_DAILY_LOG_TITLE_PROP_ID = "title"
_DAILY_LOG_DATE_PROP_ID = "u%7CdG"
_DAILY_LOG_STATUS_PROP_ID = "Wg%5Dv"
_DAILY_LOG_CATEGORY_PROP_ID = "%40CEi"
_DAILY_LOG_MEMO_PROP_ID = "rQoi"
_DAILY_LOG_STATUS_MAP = {
    "1b1f087d-08ff-4135-b3f8-50ad6ea4347d": "done",
    "3e72b76f-a917-4cbf-ad71-2ba596834b37": "doing",
    "14586de4-b42a-43c3-947c-191010ade2ef": "recorded",
}

def _prop_by_id(props: dict, prop_id: str) -> dict | None:
    """Notion page properties are keyed by (renameable) name, with the
    stable id tucked inside each value -- so looking up by id means scanning
    values, not a dict[prop_id] access."""
    for value in props.values():
        if value.get("id") == prop_id:
            return value
    return None

def pull_notion_daily_log(month: str | None = None) -> dict:
    """Import rows from the property-based Notion daily-log database (title/
    date/status/category/memo columns) into Events, one Event per row.

    Distinct from pull_notion_daily_activities: that one parses JSON
    envelopes out of page blocks; this one queries a Notion database's rows
    directly via the Data Sources API. Idempotent via events.notion_page_id
    (a page already imported is skipped on re-run), so it's safe to call
    repeatedly as the source database keeps changing.
    """
    data_source_id = settings.notion_daily_log_data_source_id
    if not data_source_id:
        return {"ok": False, "error": "NOTION_DAILY_LOG_DATA_SOURCE_ID missing"}
    if not settings.notion_token:
        return {"ok": False, "error": "Notion not connected: set up NOTION_TOKEN"}

    headers = {
        "Authorization": f"Bearer {settings.notion_token}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }

    results = []
    cursor = None
    try:
        while True:
            payload = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            r = requests.post(
                f"https://api.notion.com/v1/data_sources/{data_source_id}/query",
                headers=headers, json=payload, timeout=20,
            )
            r.raise_for_status()
            body = r.json()
            results.extend(body.get("results", []))
            if not body.get("has_more"):
                break
            cursor = body.get("next_cursor")
    except Exception as e:
        audit("pull_notion_daily_log", data_source_id, "failed", str(e))
        return {"ok": False, "error": str(e)}

    from .db import connect
    with connect() as conn:
        existing_ids = {
            row["notion_page_id"] for row in conn.execute(
                "SELECT notion_page_id FROM events WHERE notion_page_id IS NOT NULL"
            ).fetchall()
        }

    imported, skipped = 0, 0
    for row in results:
        page_id = row.get("id")
        if not page_id or page_id in existing_ids:
            skipped += 1
            continue
        props = row.get("properties", {})
        date_val = ((_prop_by_id(props, _DAILY_LOG_DATE_PROP_ID) or {}).get("date") or {}).get("start")
        if month and (not date_val or not date_val.startswith(month)):
            continue
        title_parts = (_prop_by_id(props, _DAILY_LOG_TITLE_PROP_ID) or {}).get("title", [])
        title = "".join(part.get("plain_text", "") for part in title_parts).strip()
        if not title:
            skipped += 1
            continue
        memo_parts = (_prop_by_id(props, _DAILY_LOG_MEMO_PROP_ID) or {}).get("rich_text", [])
        memo = "".join(part.get("plain_text", "") for part in memo_parts).strip()
        text = f"{title} — {memo}" if memo else title
        category = ((_prop_by_id(props, _DAILY_LOG_CATEGORY_PROP_ID) or {}).get("select") or {}).get("name")
        status_id = ((_prop_by_id(props, _DAILY_LOG_STATUS_PROP_ID) or {}).get("status") or {}).get("id")
        status = _DAILY_LOG_STATUS_MAP.get(status_id, "recorded")

        event_id = create_event(
            text, source="notion_daily_log", project=category,
            occurred_on=date_val, notion_page_id=page_id,
        )
        if status != "recorded":
            update_status(event_id, status)
        imported += 1

    audit("pull_notion_daily_log", data_source_id, "success", f"imported={imported}")
    return {"ok": True, "imported": imported, "skipped": skipped, "total_fetched": len(results)}

def _github_request(method: str, path: str, use_connector: bool, json_body: dict | None = None,
                     params: dict | None = None):
    if use_connector:
        # The connector proxy forwards to api.github.com; query params go on the path.
        if params:
            from urllib.parse import urlencode
            path = f"{path}?{urlencode(params)}"
        return connector_proxy("github", path, method=method, json_body=json_body)
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return requests.request(method, f"https://api.github.com{path}", headers=headers,
                             json=json_body, params=params, timeout=20)

def check_github() -> dict:
    """Verify the GitHub connection and configured target repository before
    any write, mirroring check_notion()'s startup-validation pattern."""
    use_connector = is_connector_available()
    repo = settings.github_repository

    if not use_connector and not settings.github_token:
        return {"ok": False, "connected": False, "error": "GitHub not connected: set up the GitHub connector or GITHUB_TOKEN"}

    try:
        me = _github_request("GET", "/user", use_connector)
        me.raise_for_status()
        identity = {"login": me.json().get("login")}
    except Exception as e:
        audit("check_github", repo, "failed", str(e))
        return {"ok": False, "connected": False, "error": str(e)}

    if not repo:
        return {"ok": False, "connected": True, "identity": identity, "error": "GITHUB_REPOSITORY missing"}

    try:
        r = _github_request("GET", f"/repos/{repo}", use_connector)
        r.raise_for_status()
    except Exception as e:
        audit("check_github", repo, "failed", f"target repo unreachable: {e}")
        return {"ok": False, "connected": True, "identity": identity, "target_repository": repo,
                "error": f"target repo unreachable: {e}"}

    audit("check_github", repo, "success", identity.get("login") or "")
    return {"ok": True, "connected": True, "identity": identity, "target_repository": repo}

def sync_github() -> dict:
    review = latest_review()
    if not review:
        return {"ok": False, "error": "no review"}
    if not settings.github_repository:
        return {"ok": False, "error": "GITHUB_REPOSITORY missing"}

    # Prefer the Replit-managed GitHub connector (no token to manage/rotate).
    # Falls back to a manually-configured GITHUB_TOKEN for portability outside Replit.
    use_connector = is_connector_available()
    if not use_connector and not settings.github_token:
        return {"ok": False, "error": "GitHub not connected: set up the GitHub connector or GITHUB_TOKEN"}

    path = f"/repos/{settings.github_repository}/contents/runtime-status/latest-review.md"
    try:
        sha = None
        get = _github_request("GET", path, use_connector, params={"ref": settings.github_branch})
        if get.status_code == 200:
            sha = get.json().get("sha")
        payload = {
            "message": f"chore: update Pulda review {review['review_date']}",
            "content": base64.b64encode(review["summary"].encode()).decode(),
            "branch": settings.github_branch,
        }
        if sha:
            payload["sha"] = sha
        r = _github_request("PUT", path, use_connector, json_body=payload)
        r.raise_for_status()
        audit("sync_github", settings.github_repository, "success", review["review_date"])
        return {"ok": True}
    except Exception as e:
        audit("sync_github", settings.github_repository, "failed", str(e))
        return {"ok": False, "error": str(e)}
