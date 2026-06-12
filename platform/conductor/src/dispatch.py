import re
import sys
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

TOOL_RESEARCH = "research"
TOOL_PLAN = "plan"
TOOL_SUMMARISE = "summarise"
TOOL_CONVERSE = "converse"
TOOL_EXECUTE = "execute"

VALID_TOOLS = {TOOL_RESEARCH, TOOL_PLAN, TOOL_SUMMARISE, TOOL_CONVERSE, TOOL_EXECUTE}

_RESEARCH_PATTERNS = [
    r"\bwhat (is|are|does|do)\b",
    r"\bexplain\b",
    r"\btell me (about|how)\b",
    r"\bwho (is|are)\b",
    r"\bwhy (is|are|does|do)\b",
    r"\bhow (does|do|did|can)\b",
    r"\bfind out\b",
    r"\bresearch\b",
    r"\blook up\b",
]

_PLAN_PATTERNS = [
    r"\b(create|make|build|design|draft|write) (a |an )?(plan|roadmap|design|spec|approach)\b",
    r"\bhow (should|would|could|can) i\b.*\b(approach|tackle|handle|address|implement)\b",
    r"\bplan\b.*\bfor\b",
    r"\bhelp me (plan|design|structure|think through|figure out)\b",
    r"\bbreak(ing)? (down|it down)\b",
    r"\bsteps (to|for)\b",
    r"\bstrategy (for|to)\b",
]

_SUMMARISE_PATTERNS = [
    r"\bsummar(ise|ize)\b",
    r"\btl;?dr\b",
    r"\bkey (points|takeaways|findings|insights)\b",
    r"\bshorten\b",
    r"\bbriefly\b",
    r"\bcondense\b",
    r"\bgist\b",
    r"\boverview\b",
]

_EXECUTE_PATTERNS = [
    r"\bread (a |the )?(file|content|code|source)\b",
    r"\b(write|create|save) (a )?file\b",
    r"\brun (a )?(command|shell|script)\b",
    r"\bsearch the web\b",
]


def _keyword_classify(text: str) -> Optional[str]:
    lower = text.lower()
    for pattern in _EXECUTE_PATTERNS:
        if re.search(pattern, lower):
            return TOOL_EXECUTE
    for pattern in _SUMMARISE_PATTERNS:
        if re.search(pattern, lower):
            return TOOL_SUMMARISE
    for pattern in _PLAN_PATTERNS:
        if re.search(pattern, lower):
            return TOOL_PLAN
    for pattern in _RESEARCH_PATTERNS:
        if re.search(pattern, lower):
            return TOOL_RESEARCH
    return None


_CLASSIFY_PROMPT = """\
Classify the following operator message into exactly one of these categories:
- research: asking for information, explanation, or facts
- plan: asking for a plan, strategy, steps, or structured approach
- summarise: asking to summarise, condense, or extract key points
- execute: asking to perform an action (read/write files, run commands, search the web)
- converse: general conversation, asking for opinions, or anything else

Reply with only the single lowercase category word. No explanation.

Message: {message}
Category:"""


def classify_intent(message: str, *, gateway=None) -> str:
    fast = _keyword_classify(message.strip())
    if fast is not None:
        return fast

    if gateway is None:
        from gateway import complete as _complete, GatewayError
    else:
        _complete = gateway.complete
        GatewayError = Exception

    prompt = _CLASSIFY_PROMPT.format(message=message.strip())
    try:
        response = _complete(
            prompt,
            caller_id="conductor.dispatch",
            max_tokens=10,
            temperature=0.0,
            context={"purpose": "intent_classification"},
        )
        result = response.content.strip().lower().split()[0] if response.content.strip() else ""
        if result in VALID_TOOLS:
            return result
    except Exception:
        pass

    return TOOL_CONVERSE


def dispatch(
    message: str,
    context_block: str,
    history: list,
    *,
    gateway=None,
    intent_override: Optional[str] = None,
) -> dict:
    intent = intent_override or classify_intent(message, gateway=gateway)

    try:
        if intent == TOOL_RESEARCH:
            from tools.research import run as research_run
            response = research_run(message, context_block=context_block, gateway=gateway)
        elif intent == TOOL_PLAN:
            from tools.plan import run as plan_run
            response = plan_run(message, context_block=context_block, gateway=gateway)
        elif intent == TOOL_SUMMARISE:
            from tools.summarise import run as summarise_run
            response = summarise_run(message, context_block=context_block, history=history, gateway=gateway)
        elif intent == TOOL_EXECUTE:
            from tools.execute import run as execute_run
            response = execute_run(message, context_block=context_block, gateway=gateway)
        else:
            from tools.converse import run as converse_run
            response = converse_run(message, context_block=context_block, history=history, gateway=gateway)
    except Exception:
        response = "I'm sorry, I couldn't reach the AI model gateway. Please check that Ollama (or your configured model provider) is running and try again."

    return {
        "intent": intent,
        "response": response,
        "tool": intent,
    }
