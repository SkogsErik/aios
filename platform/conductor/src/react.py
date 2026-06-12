from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

from tools.base import ToolResult
from tools.registry import ToolRegistry, ToolExecutor

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in sys.path:
    sys.path.insert(0, str(_GATEWAY_SRC))

REACT_SYSTEM_TPL = """\
You are a {role} agent. Your goal is:

{goal}

You have access to the following tools:

{tool_descriptions}

Context:
{wyrd_context}

Prior results from earlier plan steps:
{prior_results}

You work in a ReAct loop:
1. Think about the current situation based on the goal and context.
2. Decide on the next action: use a tool or provide the final answer.
3. If using a tool, observe the result and decide the next step.
4. When the goal is met, provide the final answer to the operator.

Previous steps:
{step_history}

{current_observation}

IMPORTANT: Once you have achieved the goal, respond with a final answer immediately.
Do not call additional tools after the goal is met.

Respond with EXACTLY ONE of the following formats:

To call a tool:
{{"action": "tool_call", "tool": "<tool_name>", "params": {{...}}}}

To provide the final answer:
{{"action": "final", "answer": "<your answer to the operator>"}}

Do not include any text before or after the JSON object.
"""

_MAX_STEPS = 20


def _find_json_object(text: str) -> str | None:
    """Extract the first top-level JSON object from text, handling nested braces."""
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


def _parse_react_response(text: str) -> dict[str, Any] | None:
    text = text.strip()
    raw = _find_json_object(text)
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


class ReactRunner:
    def __init__(
        self,
        gateway=None,
        max_steps: int = _MAX_STEPS,
        confirmation_gate: Callable[[str, str], bool] | None = None,
        model: str | None = None,
    ) -> None:
        if gateway is None:
            from gateway import complete as _complete
            self._complete = _complete
        else:
            self._complete = gateway.complete
        self._max_steps = max_steps
        self._step_history: list[dict[str, Any]] = []
        self._confirmation_gate = confirmation_gate
        self._model = model

    def run(
        self,
        goal: str,
        role: str,
        wyrd_context: str = "",
        prior_results: str = "",
    ) -> ToolResult:
        if self._confirmation_gate is not None:
            ToolExecutor.set_confirmation_gate(self._confirmation_gate)

        for step_num in range(1, self._max_steps + 1):
            tool_descriptions = self._build_tool_descriptions(role)
            step_history_str = self._format_step_history()
            current_obs = self._format_current_observation()

            prompt = REACT_SYSTEM_TPL.format(
                role=role,
                goal=goal,
                tool_descriptions=tool_descriptions,
                wyrd_context=wyrd_context or "(none)",
                prior_results=prior_results or "(none)",
                step_history=step_history_str or "(no steps yet)",
                current_observation=current_obs,
            )

            response = self._complete(
                prompt,
                caller_id="conductor.react",
                max_tokens=1000,
                temperature=0.0,
                context={"purpose": "react_loop", "role": role, "step": step_num},
                model=self._model,
            )
            raw = response.content.strip()
            parsed = _parse_react_response(raw)

            if parsed is None:
                self._step_history.append({
                    "step": step_num,
                    "action": "parse_error",
                    "raw": raw[:200],
                    "result": "Could not parse model response",
                })
                continue

            action = parsed.get("action", "")
            params = parsed.get("params", {})

            if action == "final":
                answer = parsed.get("answer", "")
                self._step_history.append({
                    "step": step_num,
                    "action": "final",
                    "answer": answer,
                })
                return ToolResult(success=True, output=answer)

            tool_name = ""
            if action == "tool_call":
                tool_name = parsed.get("tool", "")
            elif ToolRegistry.get(action) is not None:
                tool_name = action
                params = parsed.get("params", {})

            if tool_name:
                tool_result = ToolExecutor.execute(tool_name, params, role=role)

                self._step_history.append({
                    "step": step_num,
                    "action": "tool_call",
                    "tool": tool_name,
                    "params": params,
                    "result": tool_result.output[:500] if tool_result.success else tool_result.error,
                    "success": tool_result.success,
                })
                continue

            self._step_history.append({
                "step": step_num,
                "action": "unknown",
                "raw": raw[:200],
                "result": f"Unknown action: {action}",
            })

        return ToolResult(
            success=False,
            output="",
            error=f"ReAct loop reached maximum {self._max_steps} steps without a final answer",
        )

    def _build_tool_descriptions(self, role: str | None) -> str:
        try:
            from agents import RoleRegistry
            role_obj = RoleRegistry.get(role) if role else None
        except Exception:
            role_obj = None

        tools = ToolRegistry.list_tools()
        lines = []
        for t in tools:
            allowed = True
            if role_obj:
                allowed_check, _ = RoleRegistry.validate_tool_access(role, t.name) if role else (True, None)
                allowed = allowed_check
            if not allowed:
                continue
            params_desc = ", ".join(
                f"{k} ({v.get('type', 'any')})"
                for k, v in t.parameters.get("properties", {}).items()
            )
            lines.append(f"- {t.name}: {t.description}")
            if params_desc:
                lines.append(f"  Parameters: {params_desc}")
            lines.append("")
        return "\n".join(lines).strip()

    def _format_step_history(self) -> str:
        if not self._step_history:
            return ""
        lines = []
        for s in self._step_history:
            if s.get("action") == "tool_call":
                lines.append(
                    f"  Step {s['step']}: Called tool '{s.get('tool', '?')}' "
                    f"with params {s.get('params', {})}"
                )
                if s.get("success"):
                    lines.append(f"    Result: {s['result'][:200]}")
                else:
                    lines.append(f"    Error: {s['result'][:200]}")
            elif s.get("action") == "final":
                lines.append(f"  Step {s['step']}: Final answer")
            else:
                lines.append(f"  Step {s['step']}: {s.get('action', '?')}")
        return "\n".join(lines)

    def _format_current_observation(self) -> str:
        if not self._step_history:
            return "Current state: No actions taken yet."
        last = self._step_history[-1]
        if last.get("action") == "tool_call":
            if last.get("success"):
                return f"Last tool result ({last.get('tool', '?')}): {last['result'][:500]}"
            else:
                return f"Last tool error ({last.get('tool', '?')}): {last['result'][:500]}"
        return "Current state: Awaiting next action."

    @property
    def step_history(self) -> list[dict[str, Any]]:
        return list(self._step_history)
