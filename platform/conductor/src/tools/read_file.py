from __future__ import annotations

from pathlib import Path

from .base import BaseTool, ToolResult


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file from the local filesystem."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to read.",
            },
        },
        "required": ["path"],
    }

    def __init__(self, allowed_prefixes: list[Path] | None = None) -> None:
        self._allowed_prefixes = allowed_prefixes or []

    def run(self, **params: str | int | float | bool) -> ToolResult:
        raw = params.get("path", "")
        if not isinstance(raw, str) or not raw.strip():
            return ToolResult(success=False, output="", error="path must be a non-empty string")
        path = Path(raw).resolve()
        if self._allowed_prefixes and not any(
            str(path).startswith(str(p.resolve())) for p in self._allowed_prefixes
        ):
            return ToolResult(
                success=False,
                output="",
                error=f"Access denied: path '{path}' is outside the allowed directory",
            )
        if not path.exists():
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        if not path.is_file():
            return ToolResult(success=False, output="", error=f"Not a file: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
