from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

from .base import BaseTool, ToolResult
from .read_file import ReadFileTool
from .write_file import WriteFileTool
from .run_shell import RunShellTool
from .web_search import WebSearchTool

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_OBS_DIR = _REPO_ROOT / "platform" / "knowledge" / "observations"


class ToolRegistry:
    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[BaseTool]:
        return list(cls._tools.values())

    @classmethod
    def tool_descriptions(cls) -> str:
        lines = ["Available tools:", ""]
        for t in cls._tools.values():
            params_desc = ", ".join(
                f"{k} ({v.get('type', 'any')})"
                for k, v in t.parameters.get("properties", {}).items()
            )
            lines.append(f"- {t.name}: {t.description}")
            if params_desc:
                lines.append(f"  Parameters: {params_desc}")
            lines.append("")
        return "\n".join(lines).strip()


def _default_registry() -> ToolRegistry:
    repo = Path(__file__).resolve().parent.parent.parent.parent.parent
    allowed = [repo]
    ToolRegistry.register(ReadFileTool(allowed_prefixes=allowed))
    ToolRegistry.register(WriteFileTool(allowed_prefixes=allowed))
    ToolRegistry.register(RunShellTool())
    ToolRegistry.register(WebSearchTool())


_default_registry()


class ToolExecutor:
    confirmation_gate: Callable[[str, str], bool] | None = None

    @staticmethod
    def set_confirmation_gate(gate: Callable[[str, str], bool]) -> None:
        ToolExecutor.confirmation_gate = gate

    @staticmethod
    def execute(tool_name: str, params: dict[str, Any], role: str | None = None) -> ToolResult:
        tool = ToolRegistry.get(tool_name)
        if tool is None:
            return ToolResult(success=False, output="", error=f"Unknown tool: {tool_name}")

        # Step 1: Role-based access check
        if role is not None:
            from agents import RoleRegistry
            allowed, denial_reason = RoleRegistry.validate_tool_access(role, tool_name)
            if not allowed:
                return ToolResult(
                    success=False,
                    output="",
                    error=denial_reason or f"Role '{role}' cannot use tool '{tool_name}'",
                )

        # Step 2: Validate parameters
        errors = tool.validate_params(params)
        if errors:
            msg = "; ".join(errors)
            ToolExecutor._log_invocation(tool_name, params, role, ToolResult(success=False, output="", error=msg))
            return ToolResult(success=False, output="", error=msg)

        # Step 3: Check if confirmation is required
        requires_confirm = getattr(tool, "REQUIRES_CONFIRMATION", False)
        if requires_confirm and ToolExecutor.confirmation_gate is not None:
            summary = f"Tool: {tool_name}\nParams: {params}"
            if not ToolExecutor.confirmation_gate(tool_name, summary):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Operator denied confirmation for {tool_name}",
                )

        # Step 4: Execute
        result = tool.run(**params)

        # Step 5: Log
        ToolExecutor._log_invocation(tool_name, params, role, result)
        return result

    @staticmethod
    def _log_invocation(tool_name: str, params: dict[str, Any], role: str | None, result: ToolResult) -> None:
        now = datetime.datetime.now()
        obs_file = _OBS_DIR / now.strftime("%Y/%m") / f"{now.strftime('%Y-%m-%d')}.yaml"
        obs_file.parent.mkdir(parents=True, exist_ok=True)
        safe_params = {k: v for k, v in params.items() if k not in ("content",)}
        entry = {
            "id": f"TOL-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}",
            "timestamp": now.isoformat(),
            "type": "note",
            "source_mechanism": "tool",
            "source_component": tool_name,
            "role": role,
            "summary": f"[{role or 'assistant'}:{tool_name}] success={result.success}, output={result.output[:200]}",
            "params": safe_params,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error,
        }
        records: list[dict] = []
        if obs_file.exists():
            with open(obs_file) as f:
                records = yaml.safe_load(f) or []
        records.append(entry)
        with open(obs_file, "w") as f:
            yaml.dump(records, f, default_flow_style=False, sort_keys=False)
