import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pulda import ai_provider


def _settings(**overrides):
    base = {"ai_provider": "auto", "anthropic_api_key": "", "anthropic_model": "claude-sonnet-5"}
    base.update(overrides)
    return SimpleNamespace(**base)


def test_get_provider_defaults_to_rule_based_without_key(monkeypatch):
    monkeypatch.setattr(ai_provider, "settings", _settings())
    provider = ai_provider.get_provider()
    assert isinstance(provider, ai_provider.RuleBasedProvider)
    assert provider.name == "rule-based-v0"


def test_get_provider_uses_anthropic_when_key_present(monkeypatch):
    monkeypatch.setattr(ai_provider, "settings", _settings(anthropic_api_key="sk-test"))
    provider = ai_provider.get_provider()
    assert isinstance(provider, ai_provider.AnthropicProvider)
    assert provider.model == "claude-sonnet-5"


def test_get_provider_rule_based_forced_ignores_key(monkeypatch):
    monkeypatch.setattr(ai_provider, "settings", _settings(ai_provider="rule-based", anthropic_api_key="sk-test"))
    provider = ai_provider.get_provider()
    assert isinstance(provider, ai_provider.RuleBasedProvider)


def test_get_provider_anthropic_forced_without_key_raises(monkeypatch):
    monkeypatch.setattr(ai_provider, "settings", _settings(ai_provider="anthropic"))
    try:
        ai_provider.get_provider()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def _fake_response(payload: dict):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"content": [{"type": "text", "text": json.dumps(payload)}]}
    return response


def test_anthropic_provider_parses_response():
    payload = {
        "role": "회사", "area": "프로젝트", "kind": "task_candidate",
        "urgency": 4, "importance": 5, "due_date": "2026-08-20",
        "scheduled_at": None, "confidence": 0.9,
    }
    with patch.object(ai_provider.requests, "post", return_value=_fake_response(payload)) as mock_post:
        provider = ai_provider.AnthropicProvider("sk-test", "claude-sonnet-5")
        result = provider.interpret("VIP 고객 홈페이지 검토")

    assert result.classification.role == "회사"
    assert result.classification.area == "프로젝트"
    assert result.classification.urgency == 4
    assert result.classification.importance == 5
    assert result.classification.due_date == "2026-08-20"
    assert result.confidence == 0.9
    assert result.model == "anthropic:claude-sonnet-5"
    assert mock_post.call_args.kwargs["headers"]["x-api-key"] == "sk-test"


def test_anthropic_provider_clamps_and_defaults_out_of_range_values():
    payload = {
        "role": "알수없음", "area": "알수없음", "kind": "알수없음",
        "urgency": 9, "importance": -3, "due_date": None,
        "scheduled_at": None, "confidence": 1.5,
    }
    with patch.object(ai_provider.requests, "post", return_value=_fake_response(payload)):
        provider = ai_provider.AnthropicProvider("sk-test", "claude-sonnet-5")
        result = provider.interpret("애매한 입력")

    assert result.classification.role == "개인"
    assert result.classification.area == "운영"
    assert result.classification.kind == "event"
    assert result.classification.urgency == 5
    assert result.classification.importance == 1
    assert result.confidence == 1.0
