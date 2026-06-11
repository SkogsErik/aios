"""
tools/research.py — Research tool for the Conductor.

Handles intent class: research
"What is X?", "Explain Y", "Tell me about Z", "How does X work?"

Assembles a context-injected prompt, calls the model gateway, and returns
a structured response string.

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

_RESEARCH_SYSTEM = """\
You are a knowledgeable assistant helping the operator research a topic.
Provide a clear, accurate, and well-structured response.
Be concise but thorough. Use bullet points or sections when appropriate.
If you are uncertain about something, say so clearly."""


def run(message: str, *, context_block: str = "", gateway=None) -> str:
    """
    Execute a research request.

    Parameters
    ----------
    message : str
        The operator's research question.
    context_block : str
        Pre-assembled Wyrd context block (prepended to the prompt).
    gateway : module, optional
        Gateway module (injectable for testing).

    Returns
    -------
    str
        The model's research response.
    """
    if gateway is None:
        from gateway import complete as _complete
    else:
        _complete = gateway.complete

    parts = [_RESEARCH_SYSTEM]
    if context_block:
        parts.append(context_block)
    parts.append(f"Research request: {message}")
    prompt = "\n\n".join(parts)

    response = _complete(
        prompt,
        caller_id="conductor.tools.research",
        context={"tool": "research", "message_preview": message[:100]},
    )
    return response.content
