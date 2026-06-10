"""
gateway.py — AIOS Model Gateway core module

Mediates all AI model access. Every call to an AI model must flow through
this module. Direct provider calls are prohibited (ADR-002).

Public interface:
  complete(prompt, *, model, caller_id, ...) -> GatewayResponse

Capability: CAP-003 (AI and Model Management)
Pattern defined by: ADR-002 — Model Gateway Pattern
Technology selected by: ADR-006 — Model Gateway Technology Selection
"""

import time
from pathlib import Path
from typing import Any, Optional

from config_loader import get_audit_log_path, load_config
import audit_log as audit_mod

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class GatewayResponse:
    """Structured response returned by complete()."""

    def __init__(
        self,
        call_id: str,
        content: str,
        model: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        total_tokens: Optional[int],
        cost_usd: Optional[float],
        latency_ms: int,
    ):
        self.call_id = call_id
        self.content = content
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.cost_usd = cost_usd
        self.latency_ms = latency_ms

    def __repr__(self) -> str:
        return (
            f"GatewayResponse(call_id={self.call_id!r}, model={self.model!r}, "
            f"tokens={self.total_tokens}, latency_ms={self.latency_ms})"
        )


class GatewayError(Exception):
    """Raised when the gateway cannot fulfil a request."""
    def __init__(self, message: str, status: str = "error"):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_config: dict[str, Any] = {}
_rate_limiter_state: dict[str, Any] = {"count": 0, "window_start": 0.0}


def _get_config() -> dict[str, Any]:
    """Lazily load configuration on first call."""
    global _config
    if not _config:
        _config = load_config()
    return _config


# ---------------------------------------------------------------------------
# Rate limiting (simple token-bucket per minute)
# ---------------------------------------------------------------------------

def _check_rate_limit(config: dict) -> None:
    """Raise GatewayError if the per-minute request limit is exceeded."""
    limit = config.get("rate_limit", {}).get("requests_per_minute", 60)
    now = time.time()
    state = _rate_limiter_state

    if now - state["window_start"] >= 60.0:
        state["count"] = 0
        state["window_start"] = now

    if state["count"] >= limit:
        raise GatewayError(
            f"Rate limit exceeded ({limit} requests/minute).",
            status="rate_limited",
        )
    state["count"] += 1


# ---------------------------------------------------------------------------
# Safety filtering (basic — extensible)
# ---------------------------------------------------------------------------

_BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "jailbreak",
]


def _safety_check_prompt(prompt: str, config: dict) -> None:
    """Raise GatewayError if the prompt matches a blocked pattern."""
    if not config.get("safety", {}).get("enabled", True):
        return
    lower = prompt.lower()
    for pattern in _BLOCKED_PATTERNS:
        if pattern in lower:
            raise GatewayError(
                f"Prompt blocked by safety filter (matched: {pattern!r}).",
                status="safety_blocked",
            )


# ---------------------------------------------------------------------------
# Core gateway function
# ---------------------------------------------------------------------------

def complete(
    prompt: str,
    *,
    model: Optional[str] = None,
    caller_id: str = "operator",
    context: Optional[dict] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    config_path: Optional[Path] = None,
    _provider: Optional[Any] = None,  # injection point for testing
) -> GatewayResponse:
    """
    Send a completion request through the model gateway.

    Parameters
    ----------
    prompt : str
        The user prompt to send to the model.
    model : str, optional
        LiteLLM model identifier (e.g. "ollama/llama3.2"). Defaults to the
        configured default_model.
    caller_id : str
        Traceability identifier for the calling workflow or operator.
    context : dict, optional
        Arbitrary metadata recorded in the audit log for traceability.
    max_tokens : int, optional
        Maximum tokens in the completion.
    temperature : float, optional
        Sampling temperature (0.0–2.0). None uses the model default.
    config_path : Path, optional
        Override path to the gateway config file (for testing).
    _provider : callable, optional
        Injection point for tests; replaces the LiteLLM completion call.

    Returns
    -------
    GatewayResponse

    Raises
    ------
    GatewayError
        If the call is blocked by rate limiting, budget, or safety controls,
        or if the underlying model call fails.
    """
    cfg = load_config(config_path) if config_path else _get_config()
    resolved_model = model or cfg.get("default_model", "ollama/llama3.2")
    log_path = get_audit_log_path(cfg)
    log_content = cfg.get("audit", {}).get("log_content", False)

    # Pre-call controls
    _check_rate_limit(cfg)
    _safety_check_prompt(prompt, cfg)

    # Model call
    start = time.time()
    error_msg: Optional[str] = None
    status = "success"
    content = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None

    try:
        if _provider is not None:
            # Test injection: _provider is a callable that accepts (model, messages, **kwargs)
            result = _provider(
                model=resolved_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            import litellm
            _configure_litellm(cfg)
            kwargs: dict[str, Any] = {
                "model": resolved_model,
                "messages": [{"role": "user", "content": prompt}],
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if temperature is not None:
                kwargs["temperature"] = temperature
            result = litellm.completion(**kwargs)

        content = result.choices[0].message.content or ""
        usage = getattr(result, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
        cost_usd = getattr(result, "_hidden_params", {}).get("response_cost", None)

    except GatewayError:
        raise
    except Exception as exc:
        error_msg = str(exc)
        status = "error"

    latency_ms = int((time.time() - start) * 1000)

    call_id = audit_mod.write_entry(
        log_path,
        caller_id=caller_id,
        model=resolved_model,
        status=status,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        error=error_msg,
        context=context,
        prompt_preview=prompt[:200] if log_content else None,
        completion_preview=content[:200] if log_content and content else None,
    )

    if status == "error":
        raise GatewayError(f"Model call failed: {error_msg}")

    return GatewayResponse(
        call_id=call_id,
        content=content,
        model=resolved_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# LiteLLM provider configuration
# ---------------------------------------------------------------------------

def _configure_litellm(config: dict) -> None:
    """Apply provider configuration to LiteLLM from the gateway config."""
    import litellm
    import os

    providers = config.get("providers", {})

    # Ollama: set api_base via litellm
    ollama_cfg = providers.get("ollama", {})
    if "api_base" in ollama_cfg:
        # LiteLLM reads OLLAMA_API_BASE or the api_base kwarg per-call.
        # Setting the environment variable here ensures it is picked up globally.
        os.environ.setdefault("OLLAMA_API_BASE", ollama_cfg["api_base"])

    # OpenAI: load API key from env if configured
    openai_cfg = providers.get("openai", {})
    if "api_key_env" in openai_cfg:
        key = os.environ.get(openai_cfg["api_key_env"])
        if key:
            litellm.api_key = key

    # Anthropic: load API key from env if configured
    anthropic_cfg = providers.get("anthropic", {})
    if "api_key_env" in anthropic_cfg:
        key = os.environ.get(anthropic_cfg["api_key_env"])
        if key:
            os.environ.setdefault("ANTHROPIC_API_KEY", key)
