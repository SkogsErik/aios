from tools.registry import ToolRegistry, ToolExecutor
from tools.base import BaseTool, ToolResult


class _TestTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    parameters = {
        "type": "object",
        "properties": {
            "msg": {"type": "string"},
        },
        "required": ["msg"],
    }

    def run(self, **params):
        return ToolResult(success=True, output=params.get("msg", "ok"))


class TestToolRegistry:
    def test_register_and_get(self):
        ToolRegistry.register(_TestTool())
        tool = ToolRegistry.get("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"

    def test_get_unknown_returns_none(self):
        assert ToolRegistry.get("nonexistent") is None

    def test_list_tools(self):
        tools = ToolRegistry.list_tools()
        names = [t.name for t in tools]
        assert "read_file" in names
        assert "write_file" in names
        assert "run_shell" in names
        assert "web_search" in names

    def test_tool_descriptions(self):
        desc = ToolRegistry.tool_descriptions()
        assert "read_file" in desc
        assert "write_file" in desc
        assert "run_shell" in desc
        assert "web_search" in desc

    def test_validate_params(self):
        tool = ToolRegistry.get("read_file")
        assert tool is not None
        errors = tool.validate_params({})
        assert len(errors) > 0
        errors = tool.validate_params({"path": "/tmp/test"})
        assert errors == []


class TestToolExecutor:
    def test_execute_known_tool(self):
        result = ToolExecutor.execute("read_file", {"path": __file__})
        assert result.success is True
        assert "ToolResult" in result.output

    def test_execute_unknown_tool(self):
        result = ToolExecutor.execute("nonexistent", {})
        assert result.success is False
        assert "Unknown tool" in (result.error or "")

    def test_execute_with_invalid_params(self):
        result = ToolExecutor.execute("read_file", {})
        assert result.success is False
        assert "path" in (result.error or "")

    def test_execute_shell_success(self):
        result = ToolExecutor.execute("run_shell", {"command": "echo ok"})
        assert result.success is True
        assert result.output == "ok"
