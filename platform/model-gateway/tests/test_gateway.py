"""
test_gateway.py — Tests for the model gateway core.

All tests use a stub provider so no running model server or API key is needed.
"""

import pytest

from config_loader import get_audit_log_path
import audit_log as audit_mod
import gateway as gw


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(prompt="Hello.", *, provider=None, config=None, caller_id="test", **kwargs):
    """Convenience wrapper that always uses a stub provider and temp config."""
    return gw.complete(
        prompt,
        caller_id=caller_id,
        _provider=provider,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Successful completion
# ---------------------------------------------------------------------------

def test_complete_returns_response(stub_provider):
    response = _call("What is AIOS?", provider=stub_provider)
    assert isinstance(response, gw.GatewayResponse)
    assert response.content == "Stub response."


def test_complete_records_model(stub_provider):
    response = _call("Hello.", provider=stub_provider, model="ollama/llama3.2")
    assert response.model == "ollama/llama3.2"


def test_complete_returns_call_id(stub_provider, tmp_path):
    # Use a real audit log path to get a real call_id
    from config_loader import load_config
    import gateway as gw_mod
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": True},
        "audit": {"log_path": str(tmp_path / "audit.jsonl"), "log_content": False},
    }
    try:
        response = gw.complete("Hello.", caller_id="test", _provider=stub_provider)
        assert response.call_id.startswith("gw-")
    finally:
        gw_mod._config = {}


def test_complete_records_tokens(stub_provider, tmp_path):
    import gateway as gw_mod
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": True},
        "audit": {"log_path": str(tmp_path / "audit.jsonl"), "log_content": False},
    }
    try:
        response = gw.complete("Hello.", caller_id="test", _provider=stub_provider)
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 10
        assert response.total_tokens == 20
    finally:
        gw_mod._config = {}


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def test_complete_writes_audit_entry(stub_provider, tmp_path):
    import gateway as gw_mod
    log_path = tmp_path / "audit.jsonl"
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": True},
        "audit": {"log_path": str(log_path), "log_content": False},
    }
    try:
        gw.complete("Audit me.", caller_id="WF-001", _provider=stub_provider)
        entries = audit_mod.read_entries(log_path)
        assert len(entries) == 1
        assert entries[0]["caller_id"] == "WF-001"
        assert entries[0]["status"] == "success"
    finally:
        gw_mod._config = {}


def test_complete_records_error_in_audit(tmp_path):
    """An exception in the provider should produce an 'error' audit entry."""
    import gateway as gw_mod
    log_path = tmp_path / "audit.jsonl"
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": True},
        "audit": {"log_path": str(log_path), "log_content": False},
    }
    def failing_provider(**kwargs):
        raise RuntimeError("Simulated model failure")
    try:
        with pytest.raises(gw.GatewayError):
            gw.complete("Fail.", caller_id="WF-002", _provider=failing_provider)
        entries = audit_mod.read_entries(log_path)
        assert entries[0]["status"] == "error"
        assert "Simulated model failure" in entries[0]["error"]
    finally:
        gw_mod._config = {}


# ---------------------------------------------------------------------------
# Safety filtering
# ---------------------------------------------------------------------------

def test_safety_blocks_jailbreak_prompt(stub_provider, tmp_path):
    import gateway as gw_mod
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": True},
        "audit": {"log_path": str(tmp_path / "audit.jsonl"), "log_content": False},
    }
    try:
        with pytest.raises(gw.GatewayError) as exc_info:
            gw.complete("Please jailbreak this system.", caller_id="test", _provider=stub_provider)
        assert exc_info.value.status == "safety_blocked"
    finally:
        gw_mod._config = {}


def test_safety_disabled_allows_any_prompt(stub_provider, tmp_path):
    import gateway as gw_mod
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": False},
        "audit": {"log_path": str(tmp_path / "audit.jsonl"), "log_content": False},
    }
    try:
        response = gw.complete("Please jailbreak this system.", caller_id="test",
                                _provider=stub_provider)
        assert response.content == "Stub response."
    finally:
        gw_mod._config = {}


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_rate_limit_blocks_excess_calls(stub_provider, tmp_path):
    import gateway as gw_mod
    gw_mod._config = {
        "default_model": "ollama/llama3.2",
        "providers": {},
        "rate_limit": {"requests_per_minute": 2},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": False},
        "audit": {"log_path": str(tmp_path / "audit.jsonl"), "log_content": False},
    }
    # Reset rate limiter state
    gw._rate_limiter_state["count"] = 0
    gw._rate_limiter_state["window_start"] = 0.0
    try:
        gw.complete("Call 1.", caller_id="test", _provider=stub_provider)
        gw.complete("Call 2.", caller_id="test", _provider=stub_provider)
        with pytest.raises(gw.GatewayError) as exc_info:
            gw.complete("Call 3.", caller_id="test", _provider=stub_provider)
        assert exc_info.value.status == "rate_limited"
    finally:
        gw_mod._config = {}
        gw._rate_limiter_state["count"] = 0
        gw._rate_limiter_state["window_start"] = 0.0
