"""Minimal client for calling Replit-managed connectors (e.g. Notion) from
server-side Python code, without requiring a Node.js runtime.

This mirrors the protocol used by the official `@replit/connectors-sdk`
JS package: resolve a short-lived Replit identity token, then call the
connectors proxy at `{REPLIT_CONNECTORS_HOSTNAME}/api/v2/proxy/<path>`
with a `Connector-Name` header identifying the target service.
"""
import os
import subprocess

import requests

DEFAULT_CONNECTORS_HOST = "connectors.replit.com"


def _resolve_audience() -> str:
    audience = os.getenv("REPLIT_CONNECTORS_AUDIENCE")
    if audience:
        if audience.startswith("http://") or audience.startswith("https://"):
            return audience
        return f"https://{audience}"
    return f"https://{DEFAULT_CONNECTORS_HOST}"


def _resolve_identity_token() -> str:
    replit_binary = os.getenv("REPLIT_CLI", "replit")
    audience = _resolve_audience()
    try:
        result = subprocess.run(
            [replit_binary, "identity", "create", "--audience", audience],
            capture_output=True, text=True, timeout=10, check=True,
        )
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass  # CLI unavailable — fall through to env var strategies

    repl_identity = os.getenv("REPL_IDENTITY")
    if repl_identity:
        return f"repl {repl_identity}"

    depl_token = os.getenv("WEB_REPL_RENEWAL")
    if depl_token:
        return f"depl {depl_token}"

    raise RuntimeError(
        "Replit identity token not found. Could not run `replit identity "
        "create` and neither REPL_IDENTITY nor WEB_REPL_RENEWAL are set. "
        "Are you running this inside a Repl?"
    )


def _resolve_base_url() -> str:
    hostname = os.getenv("REPLIT_CONNECTORS_HOSTNAME")
    if hostname:
        if hostname.startswith("http://") or hostname.startswith("https://"):
            return hostname
        return f"https://{hostname}"
    return f"https://{DEFAULT_CONNECTORS_HOST}"


def _build_headers() -> dict:
    token = _resolve_identity_token()
    headers = {"Accept": "application/json"}
    if token.startswith("repl ") or token.startswith("depl "):
        headers["X-Replit-Token"] = token
    else:
        headers["Replit-Authentication"] = f"Bearer {token}"
    return headers


def is_connector_available() -> bool:
    """Best-effort check that the identity/proxy plumbing is usable here."""
    return bool(os.getenv("REPL_IDENTITY") or os.getenv("WEB_REPL_RENEWAL"))


def connector_proxy(connector_name: str, path: str, method: str = "GET",
                     json_body: dict | None = None, timeout: int = 20) -> requests.Response:
    """Call an authenticated Replit connector proxy endpoint, e.g.
    connector_proxy("notion", "/v1/search", method="POST", json_body={...}).
    """
    base_url = _resolve_base_url()
    normalized_path = path if path.startswith("/") else f"/{path}"
    url = f"{base_url}/api/v2/proxy{normalized_path}"
    headers = _build_headers()
    headers["Connector-Name"] = connector_name
    response = requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
    if response.status_code == 401:
        headers = _build_headers()
        headers["Connector-Name"] = connector_name
        response = requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
    return response
