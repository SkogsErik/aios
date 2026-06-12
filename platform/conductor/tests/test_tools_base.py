from tools.base import ToolResult, ToolCall


class TestToolResult:
    def test_default_values(self):
        r = ToolResult(success=True, output="hello")
        assert r.success is True
        assert r.output == "hello"
        assert r.error is None
        assert r.execution_time_ms == 0

    def test_to_dict_truncates_long_output(self):
        r = ToolResult(success=True, output="x" * 1000)
        d = r.to_dict()
        assert len(d["output"]) == 503  # 500 + "..."
        assert d["output"].endswith("...")

    def test_to_dict_short_output(self):
        r = ToolResult(success=True, output="ok")
        d = r.to_dict()
        assert d["output"] == "ok"

    def test_to_dict_includes_error(self):
        r = ToolResult(success=False, output="", error="something broke")
        d = r.to_dict()
        assert d["error"] == "something broke"
