from pathlib import Path

import yaml

from agents import RoleRegistry, RoleNotFoundError, RoleAccessDeniedError


class TestRoleRegistry:
    def test_list_roles(self, tmp_path):
        _write_role(tmp_path, "test_role", allowed=["read_file"], forbidden=["write_file"])
        RoleRegistry.reload(tmp_path)
        roles = RoleRegistry.list_roles()
        names = [r["role"] for r in roles]
        assert "test_role" in names

    def test_get_role(self, tmp_path):
        _write_role(tmp_path, "getter", allowed=["read_file"])
        RoleRegistry.reload(tmp_path)
        role = RoleRegistry.get("getter")
        assert role["role"] == "getter"
        assert "read_file" in role["allowed_tools"]

    def test_get_unknown_role_raises(self):
        RoleRegistry.reload()
        try:
            RoleRegistry.get("nonexistent_role")
            assert False, "Expected RoleNotFoundError"
        except RoleNotFoundError:
            pass

    def test_validate_allowed_tool(self, tmp_path):
        _write_role(tmp_path, "reader", allowed=["read_file"], forbidden=["write_file"])
        RoleRegistry.reload(tmp_path)
        allowed, reason = RoleRegistry.validate_tool_access("reader", "read_file")
        assert allowed is True
        assert reason is None

    def test_validate_forbidden_tool(self, tmp_path):
        _write_role(tmp_path, "reader", allowed=["read_file"], forbidden=["write_file"])
        RoleRegistry.reload(tmp_path)
        allowed, reason = RoleRegistry.validate_tool_access("reader", "write_file")
        assert allowed is False
        assert reason is not None

    def test_validate_unlisted_tool(self, tmp_path):
        _write_role(tmp_path, "reader", allowed=["read_file"], forbidden=[])
        RoleRegistry.reload(tmp_path)
        allowed, reason = RoleRegistry.validate_tool_access("reader", "run_shell")
        assert allowed is False
        assert "not in" in (reason or "")

    def test_executor_enforces_role(self, tmp_path):
        from tools.registry import ToolExecutor
        _write_role(tmp_path, "no_shell", allowed=["read_file"], forbidden=["run_shell"])
        RoleRegistry.reload(tmp_path)
        result = ToolExecutor.execute("run_shell", {"command": "echo hi"}, role="no_shell")
        assert result.success is False
        assert "not allowed" in (result.error or "").lower() or "cannot" in (result.error or "").lower()

    def test_executor_allows_with_role(self, tmp_path):
        from tools.registry import ToolExecutor
        _write_role(tmp_path, "reader", allowed=["read_file"], forbidden=[])
        RoleRegistry.reload(tmp_path)
        result = ToolExecutor.execute("read_file", {"path": __file__}, role="reader")
        assert result.success is True

    def test_validate_unknown_role(self):
        RoleRegistry.reload()
        allowed, reason = RoleRegistry.validate_tool_access("ghost", "read_file")
        assert allowed is False
        assert "unknown" in (reason or "").lower()

    def test_empty_agents_dir(self, tmp_path):
        RoleRegistry.reload(tmp_path)
        assert RoleRegistry.list_roles() == []


class TestDefaultRoles:
    def test_researcher_role_exists(self):
        RoleRegistry.reload()
        role = RoleRegistry.get("researcher")
        assert "read_file" in role["allowed_tools"]
        assert "web_search" in role["allowed_tools"]
        assert "write_file" in role["forbidden_actions"]

    def test_coder_role_exists(self):
        RoleRegistry.reload()
        role = RoleRegistry.get("coder")
        assert "read_file" in role["allowed_tools"]
        assert "write_file" in role["allowed_tools"]
        assert "run_shell" in role["allowed_tools"]
        assert "web_search" in role["forbidden_actions"]

    def test_synthesizer_role_exists(self):
        RoleRegistry.reload()
        role = RoleRegistry.get("synthesizer")
        assert "read_file" in role["allowed_tools"]
        assert len(role["allowed_tools"]) == 1
        assert "write_file" in role["forbidden_actions"]

    def test_all_default_roles_listed(self):
        RoleRegistry.reload()
        names = {r["role"] for r in RoleRegistry.list_roles()}
        assert names == {"researcher", "coder", "synthesizer"}


def _write_role(base: Path, name: str, allowed: list[str], forbidden: list[str] | None = None) -> Path:
    path = base / f"{name}.yaml"
    data = {
        "role": name,
        "description": f"Test role: {name}",
        "allowed_tools": allowed,
        "forbidden_actions": forbidden or [],
        "context_access": ["persona"],
        "escalation_triggers": [],
    }
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return path
