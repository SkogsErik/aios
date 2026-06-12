from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .base import ToolCall
from .registry import ToolRegistry, ToolExecutor

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

_EXECUTE_SYSTEM_TPL = """\
You are an AI assistant that can use tools to help the operator.
Available tools:

{tools}

Given the operator's request, decide which tool to use and with what parameters.
Respond with a JSON object containing:
  {{"tool": "<tool_name>", "params": {{...}}}}

Only use tools from the list above. If the request does not match any tool,
respond with {{"tool": "none", "params": {{}}}} and a brief explanation.
"""


def _find_json_object(text: str) -> str | None:
    text = text.strip()
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _parse_tool_call(text: str) -> ToolCall | None:
    text = text.strip()
    raw = _find_json_object(text)
    if raw:
        try:
            data = json.loads(raw)
            tool_name = data.get("tool", "").strip()
            params = data.get("params", {})
            if tool_name and tool_name != "none":
                return ToolCall(tool_name=tool_name, params=params)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def run(
    message: str,
    *,
    context_block: str = "",
    gateway=None,
) -> str:
    if gateway is None:
        from gateway import complete as _complete
    else:
        _complete = gateway.complete

    tools_desc = ToolRegistry.tool_descriptions()
    system_prompt = _EXECUTE_SYSTEM_TPL.format(tools=tools_desc)
    parts = [system_prompt]
    if context_block:
        parts.append(context_block)
    parts.append(f"Operator request: {message}")
    prompt = "\n\n".join(parts)

    response = _complete(
        prompt,
        caller_id="conductor.tools.execute",
        max_tokens=500,
        temperature=0.0,
        context={"tool": "execute", "message_preview": message[:100]},
    )
    raw = response.content.strip()

    tool_call = _parse_tool_call(raw)
    if tool_call is None:
        return f"I couldn't determine which tool to use for that request.\n\nModel response: {raw[:300]}"

    result = ToolExecutor.execute(tool_call.tool_name, tool_call.params)

    if result.success:
        return result.output
    return f"Tool '{tool_call.tool_name}' failed: {result.error}"
