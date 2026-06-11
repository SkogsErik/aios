"""
tools/plan.py — Plan tool for the Conductor.

Handles intent class: plan
"Plan X", "How should I approach Y", "Help me design Z"

Generates a structured, numbered plan with dependencies and next actions.

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

_PLAN_SYSTEM = """\
You are a thoughtful planning assistant helping the operator think through a task or initiative.
Generate a clear, actionable plan with numbered steps.
For each step include: what to do, why it matters, and any dependencies on previous steps.
End with a suggested first action the operator can take right now.
Be practical and specific to the operator's situation."""


def run(message: str, *, context_block: str = "", gateway=None) -> str:
    """
    Execute a planning request.

    Parameters
    ----------
    message : str
        The operator's planning request.
    context_block : str
        Pre-assembled Wyrd context block.
    gateway : module, optional
        Gateway module (injectable for testing).

    Returns
    -------
    str
        The structured plan as a string.
    """
    if gateway is None:
        from gateway import complete as _complete
    else:
        _complete = gateway.complete

    parts = [_PLAN_SYSTEM]
    if context_block:
        parts.append(context_block)
    parts.append(f"Planning request: {message}")
    prompt = "\n\n".join(parts)

    response = _complete(
        prompt,
        caller_id="conductor.tools.plan",
        context={"tool": "plan", "message_preview": message[:100]},
    )
    return response.content
