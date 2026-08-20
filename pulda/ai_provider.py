"""AI interpretation providers for the Living Loop (CR-0013).

`classifier.classify()` stays the deterministic, offline rule engine and the
safe fallback. `get_provider()` selects the active backend from settings so
an AI provider can be attached or detached without touching service.py, per
docs/governance/OPERATING-MODEL.md: "AI providers are replaceable adapters."
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

import requests

from .classifier import Classification, classify
from .config import settings

ROLES = ["가족", "회사", "성당", "개인"]
AREAS = ["재무", "건강", "관계", "학습", "프로젝트", "운영"]
KINDS = ["event", "task_candidate", "scheduled_event"]


@dataclass
class Interpretation:
    classification: Classification
    model: str
    confidence: float


class RuleBasedProvider:
    """Wraps the existing keyword-matching engine as a provider."""

    name = "rule-based-v0"

    def interpret(self, text: str, now: datetime | None = None) -> Interpretation:
        return Interpretation(classification=classify(text, now), model=self.name, confidence=0.5)


class AnthropicProvider:
    """Calls the Claude Messages API directly over HTTPS.

    Uses `requests` (already a runtime dependency) instead of the `anthropic`
    SDK so attaching this provider never requires a new package install.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = f"anthropic:{model}"

    def _system_prompt(self, now: datetime) -> str:
        return (
            "You classify a single personal Korean journal/event entry for the "
            "Pulda daily-activity system. Reply with ONLY a JSON object, no prose, "
            "no markdown fence, matching this schema exactly:\n"
            f'{{"role": one of {ROLES}, "area": one of {AREAS}, '
            f'"kind": one of {KINDS}, "urgency": integer 1-5, "importance": integer 1-5, '
            '"due_date": "YYYY-MM-DD" or null, "scheduled_at": "YYYY-MM-DDTHH:MM:SS" or null, '
            '"confidence": float between 0 and 1}\n'
            f"Current date/time (Asia/Seoul): {now.isoformat()}. Infer due_date/"
            "scheduled_at from relative Korean time expressions (e.g. 오늘, 내일, "
            "시) relative to the current date/time. If there is no clear signal, "
            "use null. Pick exactly one role and one area from the given lists."
        )

    def interpret(self, text: str, now: datetime | None = None) -> Interpretation:
        now = now or datetime.now()
        body = {
            "model": self.model,
            "max_tokens": 300,
            "system": self._system_prompt(now),
            "messages": [{"role": "user", "content": text}],
        }
        response = requests.post(
            self.API_URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        raw = "".join(
            block.get("text", "")
            for block in payload.get("content", [])
            if block.get("type") == "text"
        ).strip()
        data = json.loads(raw)
        classification = Classification(
            role=data.get("role") if data.get("role") in ROLES else "개인",
            area=data.get("area") if data.get("area") in AREAS else "운영",
            kind=data.get("kind") if data.get("kind") in KINDS else "event",
            urgency=max(1, min(5, int(data.get("urgency", 2)))),
            importance=max(1, min(5, int(data.get("importance", 2)))),
            status="inbox",
            due_date=data.get("due_date"),
            scheduled_at=data.get("scheduled_at"),
        )
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
        return Interpretation(classification=classification, model=self.name, confidence=confidence)


def get_provider():
    """Return the active AI provider per `PULDA_AI_PROVIDER`.

    - "rule-based": always the deterministic engine (used by tests/offline dev).
    - "anthropic": require and use the Claude API; raises if no key is set.
    - "auto" (default): use Claude when ANTHROPIC_API_KEY is set, else fall
      back to the rule engine — so removing the key detaches the AI backend
      without a code change.
    """
    choice = settings.ai_provider
    if choice == "rule-based":
        return RuleBasedProvider()
    if choice == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("AI provider 'anthropic' requested but ANTHROPIC_API_KEY is not set")
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    if settings.anthropic_api_key:
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    return RuleBasedProvider()
