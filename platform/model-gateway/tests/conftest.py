"""
conftest.py — Shared fixtures for model gateway tests.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def make_stub_provider(content: str = "Stub response.", tokens: int = 10):
    """
    Return a callable that mimics the litellm.completion() return value.
    Used to test the gateway without a real model or API key.
    """
    def _provider(model, messages, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content)
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=tokens,
                completion_tokens=tokens,
                total_tokens=tokens * 2,
            ),
            _hidden_params={"response_cost": 0.0},
        )
    return _provider


@pytest.fixture()
def stub_provider():
    return make_stub_provider()


@pytest.fixture()
def audit_log_path(tmp_path):
    return tmp_path / "audit" / "audit.jsonl"


@pytest.fixture()
def minimal_config(tmp_path, audit_log_path):
    """Return a minimal gateway config dict pointing to a temporary audit log."""
    return {
        "default_model": "ollama/llama3.2",
        "providers": {"ollama": {"api_base": "http://localhost:11434"}},
        "rate_limit": {"requests_per_minute": 60},
        "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
        "safety": {"enabled": True},
        "audit": {"log_path": str(audit_log_path), "log_content": False},
    }
