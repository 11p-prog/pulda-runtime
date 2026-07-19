import base64
import json
import requests
from .config import settings
from .service import audit, latest_review, capture_daily_activity
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
    cursor = None
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
                    "source_coverage", "access_gaps", "privacy_reviewed", "items",
                )}
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

        audit("pull_notion_daily_activities", page_id, "success", f"processed={len(processed)}")
        return {"ok": True, "processed": processed, "ignored": ignored}
    except Exception as e:
        audit("pull_notion_daily_activities", page_id, "failed", str(e))
        return {"ok": False, "processed": processed, "ignored": ignored, "error": str(e)}

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
