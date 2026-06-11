"""
tools/summarise.py — Summarise tool for the Conductor.

Handles intent class: summarise
"Summarise X", "TL;DR of Y", "What are the key points?"

Summarises provided content, conversation history, or a described document.

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

_SUMMARISE_SYSTEM = """\
You are a concise summarisation assistant.
Extract the key points, decisions, and action items from the provided content.
Use bullet points. Be concise — aim for 20% of the original length.
Highlight any action items or decisions separately."""

_MAX_HISTORY_TURNS = 10


def run(message: str, *, context_block: str = "", history: list = [], gateway=None) -> str:
    """
    Execute a summarisation request.

    If the message refers to the conversation history (e.g., "summarise our conversation"),
    the recent history turns are included in the prompt.

    Parameters
    ----------
    message : str
        The operator's summarisation request.
    context_block : str
        Pre-assembled Wyrd context block.
    history : list
        Session turns for conversation self-summarisation.
    gateway : module, optional
        Gateway module (injectable for testing).

    Returns
    -------
    str
        The summary string.
    """
    if gateway is None:
        from gateway import complete as _complete
    else:
        _complete = gateway.complete

    parts = [_SUMMARISE_SYSTEM]
    if context_block:
        parts.append(context_block)

    # Include recent history if the message seems to be about the conversation
    history_keywords = {"conversation", "chat", "above", "so far", "we discussed", "we've been"}
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in history_keywords) and history:
        recent = history[-_MAX_HISTORY_TURNS:]
        history_text = "\n".join(
            f"{t.get('role', 'unknown').upper()}: {t.get('content', '')}"
            for t in recent
        )
        parts.append(f"Conversation history:\n{history_text}")

    parts.append(f"Summarisation request: {message}")
    prompt = "\n\n".join(parts)

    response = _complete(
        prompt,
        caller_id="conductor.tools.summarise",
        context={"tool": "summarise", "message_preview": message[:100]},
    )
    return response.content
