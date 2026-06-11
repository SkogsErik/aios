"""
tools/converse.py — General conversation tool for the Conductor.

Handles intent class: converse (catch-all for all other operator messages).
Maintains full conversation history context for coherent multi-turn dialogue.

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

_CONVERSE_SYSTEM = """\
You are the AIOS Conductor — a thoughtful personal assistant helping the operator
manage their work, priorities, and thinking.
You have access to the operator's context (projects, goals, focus areas, persona).
Be direct, helpful, and honest. Acknowledge uncertainty.
Build on previous turns in the conversation where relevant."""

_MAX_HISTORY_TURNS = 20


def run(message: str, *, context_block: str = "", history: list = [], gateway=None) -> str:
    """
    Execute a general conversation turn.

    Includes recent conversation history in the prompt to maintain coherence
    across multi-turn sessions.

    Parameters
    ----------
    message : str
        Current operator message.
    context_block : str
        Pre-assembled Wyrd context block.
    history : list
        Previous session turns.
    gateway : module, optional
        Gateway module (injectable for testing).

    Returns
    -------
    str
        The model's response.
    """
    if gateway is None:
        from gateway import complete as _complete
    else:
        _complete = gateway.complete

    parts = [_CONVERSE_SYSTEM]
    if context_block:
        parts.append(context_block)

    # Include recent history for continuity
    if history:
        recent = history[-_MAX_HISTORY_TURNS:]
        history_text = "\n".join(
            f"{t.get('role', 'unknown').upper()}: {t.get('content', '')}"
            for t in recent
        )
        parts.append(f"Conversation so far:\n{history_text}")

    parts.append(f"OPERATOR: {message}\nASSISTANT:")
    prompt = "\n\n".join(parts)

    response = _complete(
        prompt,
        caller_id="conductor.tools.converse",
        context={"tool": "converse", "message_preview": message[:100]},
    )
    return response.content
