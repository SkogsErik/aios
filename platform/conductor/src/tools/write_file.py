from __future__ import annotations

from pathlib import Path

from .base import BaseTool, ToolResult


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file on the local filesystem. Requires operator confirmation."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
            "mode": {
                "type": "string",
                "description": "Write mode: 'overwrite' to replace existing content, 'append' to add to end.",
                "enum": ["overwrite", "append"],
            },
        },
        "required": ["path", "content"],
    }

    REQUIRES_CONFIRMATION = True

    def __init__(self, allowed_prefixes: list[Path] | None = None) -> None:
        self._allowed_prefixes = allowed_prefixes or []

    def run(self, **params: str | int | float | bool) -> ToolResult:
        raw_path = params.get("path", "")
        content = params.get("content", "")
        mode = params.get("mode", "overwrite")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return ToolResult(success=False, output="", error="path must be a non-empty string")
        if not isinstance(content, str):
            return ToolResult(success=False, output="", error="content must be a string")
        path = Path(raw_path).resolve()
        if self._allowed_prefixes and not any(
            str(path).startswith(str(p.resolve())) for p in self._allowed_prefixes
        ):
            return ToolResult(
                success=False,
                output="",
                error=f"Access denied: path '{path}' is outside the allowed directory",
            )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if mode == "append":
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} bytes to {path}",
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
