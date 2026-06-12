from __future__ import annotations

import shlex
import subprocess
import time

from .base import BaseTool, ToolResult

_BLOCKED_PREFIXES = [
    # Interactive shells
    "sh", "bash", "zsh", "fish", "dash",
    # Interactive editors
    "vim", "vi", "nano", "emacs", "ed", "ex",
    # TUI tools
    "htop", "top", "less", "more",
    # Background / daemon
    "nohup", "bg", "fg", "disown",
    # Network listeners
    "nc -l", "ncat -l", "socat",
]


class RunShellTool(BaseTool):
    name = "run_shell"
    description = "Run a shell command and return its output. Non-interactive, output-only. Timed out after 30 seconds by default."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to run.",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (1-120, default 30).",
                "default": 30,
            },
        },
        "required": ["command"],
    }

    def __init__(self, allowed_prefixes: list[str] | None = None) -> None:
        self._allowed_prefixes = allowed_prefixes or []

    def run(self, **params: str | int | float | bool) -> ToolResult:
        raw_cmd = params.get("command", "")
        timeout = int(params.get("timeout", 30))
        if not isinstance(raw_cmd, str) or not raw_cmd.strip():
            return ToolResult(success=False, output="", error="command must be a non-empty string")
        timeout = max(1, min(timeout, 120))

        # Block interactive commands
        first_token = raw_cmd.strip().split()[0] if raw_cmd.strip() else ""
        for blocked in _BLOCKED_PREFIXES:
            if first_token == blocked or raw_cmd.strip().startswith(blocked):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command '{first_token}' is blocked (interactive or daemon)",
                )

        start = time.monotonic()
        try:
            proc = subprocess.run(
                raw_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = int((time.monotonic() - start) * 1000)
            output = proc.stdout or ""
            if proc.stderr:
                output += f"\n[stderr]\n{proc.stderr}"
            return ToolResult(
                success=proc.returncode == 0,
                output=output.strip(),
                error=None if proc.returncode == 0 else f"exit code {proc.returncode}",
                execution_time_ms=elapsed,
            )
        except subprocess.TimeoutExpired:
            elapsed = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s",
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            return ToolResult(success=False, output="", error=str(e), execution_time_ms=elapsed)
