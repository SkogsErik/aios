from tools.run_shell import RunShellTool


class TestRunShellTool:
    def test_name_and_description(self):
        tool = RunShellTool()
        assert tool.name == "run_shell"

    def test_echo_command(self):
        tool = RunShellTool()
        result = tool.run(command="echo hello")
        assert result.success is True
        assert result.output == "hello"

    def test_failing_command(self):
        tool = RunShellTool()
        result = tool.run(command="false")
        assert result.success is False
        assert "exit code" in (result.error or "")

    def test_timeout_enforced(self):
        tool = RunShellTool()
        result = tool.run(command="sleep 5", timeout=1)
        assert result.success is False
        assert "timed out" in (result.error or "").lower()

    def test_blocked_interactive_shell(self):
        tool = RunShellTool()
        result = tool.run(command="bash")
        assert result.success is False
        assert "blocked" in (result.error or "").lower()

    def test_blocked_vim(self):
        tool = RunShellTool()
        result = tool.run(command="vim")
        assert result.success is False

    def test_blocked_htop(self):
        tool = RunShellTool()
        result = tool.run(command="htop")
        assert result.success is False

    def test_empty_command(self):
        tool = RunShellTool()
        result = tool.run(command="")
        assert result.success is False

    def test_timeout_clamped(self):
        tool = RunShellTool()
        result = tool.run(command="echo ok", timeout=999)
        assert result.success is True

    def test_validate_params(self):
        tool = RunShellTool()
        errors = tool.validate_params({})
        assert "command" in str(errors)
