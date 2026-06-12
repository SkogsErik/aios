from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    execution_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output[:500] + ("..." if len(self.output) > 500 else ""),
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class ToolCall:
    tool_name: str
    params: dict[str, Any]


class BaseTool(ABC):
    name: str
    description: str
    parameters: dict

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name") or not cls.name:
            cls.name = cls.__name__.lower().replace("tool", "")
        if not hasattr(cls, "description") or not cls.description:
            cls.description = cls.__doc__ or ""

    @abstractmethod
    def run(self, **params: Any) -> ToolResult:
        ...

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        schema = self.parameters
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for r in required:
            if r not in params:
                errors.append(f"Missing required parameter: {r}")
        for key, value in params.items():
            if key in properties:
                prop = properties[key]
                prop_type = prop.get("type")
                if prop_type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter '{key}' must be a string, got {type(value).__name__}")
                elif prop_type == "integer" and not isinstance(value, int):
                    errors.append(f"Parameter '{key}' must be an integer, got {type(value).__name__}")
        return errors
