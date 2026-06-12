from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"


class RoleNotFoundError(KeyError):
    pass


class RoleAccessDeniedError(PermissionError):
    def __init__(self, role: str, tool: str, message: str) -> None:
        self.role = role
        self.tool = tool
        self.message = message
        super().__init__(message)


class RoleRegistry:
    _roles: dict[str, dict[str, Any]] = {}
    _loaded: bool = False

    @classmethod
    def reload(cls, agents_dir: Path | None = None) -> None:
        cls._roles.clear()
        cls._loaded = False
        directory = agents_dir or _AGENTS_DIR
        if not directory.exists():
            return
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.yaml")):
            with open(path) as f:
                data = yaml.safe_load(f)
            if data and "role" in data:
                cls._roles[data["role"]] = data
        cls._loaded = True

    @classmethod
    def get(cls, role_name: str) -> dict[str, Any]:
        if not cls._loaded:
            cls.reload()
        role = cls._roles.get(role_name)
        if role is None:
            raise RoleNotFoundError(f"Unknown role: {role_name}")
        return role

    @classmethod
    def list_roles(cls) -> list[dict[str, Any]]:
        if not cls._loaded:
            cls.reload()
        return list(cls._roles.values())

    @classmethod
    def validate_tool_access(cls, role_name: str, tool_name: str) -> tuple[bool, str | None]:
        try:
            role = cls.get(role_name)
        except RoleNotFoundError:
            return False, f"Unknown role: {role_name}"

        if tool_name in role.get("forbidden_actions", []):
            for trigger in role.get("escalation_triggers", []):
                if tool_name in trigger.get("action", "").lower():
                    return False, trigger.get("response", f"Role '{role_name}' cannot use tool '{tool_name}'")
            return False, f"Role '{role_name}' is not allowed to use tool '{tool_name}'"

        if tool_name not in role.get("allowed_tools", []):
            return False, f"Tool '{tool_name}' is not in role '{role_name}' allowed_tools"

        return True, None


RoleRegistry.reload()
