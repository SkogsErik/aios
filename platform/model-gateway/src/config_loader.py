"""
config_loader.py — Gateway configuration loading

Loads and validates gateway-config.yaml. Falls back to safe defaults when
no config file is present so the gateway can operate in test environments
without a config file on disk.

Capability: CAP-003 (AI and Model Management)
Defined by: ADR-006 — Model Gateway Technology Selection
"""

from pathlib import Path
from typing import Any

import yaml

# Default config file location (relative to this module's parent directory)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "gateway-config.yaml"

# Built-in defaults — used when a config file is absent or a key is missing
_DEFAULTS: dict[str, Any] = {
    "default_model": "ollama/llama3.2",
    "providers": {
        "ollama": {"api_base": "http://localhost:11434"},
    },
    "rate_limit": {"requests_per_minute": 60},
    "cost": {"max_usd_per_day": 0.0, "block_on_budget_exceeded": False},
    "safety": {"enabled": True},
    "audit": {"log_path": "audit/audit.jsonl", "log_content": False},
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Return a new dict with override merged on top of base (deep for nested dicts)."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load the gateway configuration from disk, merging with built-in defaults.

    If no config file exists at the given path (or the default path), returns
    the built-in defaults unchanged — useful for test environments.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return dict(_DEFAULTS)
    with path.open("r", encoding="utf-8") as f:
        on_disk = yaml.safe_load(f) or {}
    return _deep_merge(_DEFAULTS, on_disk)


def get_audit_log_path(config: dict[str, Any]) -> Path:
    """Resolve the audit log path from config, relative to the gateway root."""
    raw = config.get("audit", {}).get("log_path", _DEFAULTS["audit"]["log_path"])
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).parent.parent / path
    return path
