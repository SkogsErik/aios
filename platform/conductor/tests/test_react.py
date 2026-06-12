from react import ReactRunner, _parse_react_response


class _MockResponse:
    def __init__(self, content: str):
        self.content = content


class _MockGateway:
    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or []
        self._index = 0
        self.calls = []

    def complete(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt[:100], **kwargs})
        if self._index < len(self._responses):
            resp = self._responses[self._index]
            self._index += 1
            return _MockResponse(resp)
        return _MockResponse('{"action": "final", "answer": "Default answer."}')


class TestParseReactResponse:
    def test_parses_tool_call(self):
        result = _parse_react_response('{"action": "tool_call", "tool": "read_file", "params": {"path": "/tmp/x"}}')
        assert result is not None
        assert result["action"] == "tool_call"
        assert result["tool"] == "read_file"

    def test_parses_final_answer(self):
        result = _parse_react_response('{"action": "final", "answer": "Done."}')
        assert result["action"] == "final"
        assert result["answer"] == "Done."

    def test_returns_none_for_garbage(self):
        assert _parse_react_response("hello world") is None

    def test_extracts_json_from_surrounding_text(self):
        result = _parse_react_response(
            'Here is my decision:\n{"action": "final", "answer": "All set."}\n'
        )
        assert result is not None
        assert result["answer"] == "All set."

    def test_parses_multiline_answer_with_newlines(self):
        result = _parse_react_response('{"action": "final", "answer": "Line one\nLine two\nLine three"}')
        assert result is not None
        assert result["action"] == "final"
        assert "Line one" in result["answer"]


class TestReactRunner:
    def test_immediate_final_answer(self):
        gw = _MockGateway(['{"action": "final", "answer": "Task completed."}'])
        runner = ReactRunner(gateway=gw, max_steps=5)
        result = runner.run(goal="Say hello", role="coder")
        assert result.success is True
        assert result.output == "Task completed."
        assert len(gw.calls) == 1

    def test_single_tool_call_then_final(self):
        gw = _MockGateway([
            '{"action": "tool_call", "tool": "run_shell", "params": {"command": "echo hello"}}',
            '{"action": "final", "answer": "Done."}',
        ])
        runner = ReactRunner(gateway=gw, max_steps=5)
        result = runner.run(goal="Run a command", role="coder")
        assert result.success is True
        assert len(gw.calls) == 2
        assert len(runner.step_history) == 2
        assert runner.step_history[0]["action"] == "tool_call"
        assert runner.step_history[1]["action"] == "final"

    def test_parse_error_continues(self):
        gw = _MockGateway([
            "garbage response",
            '{"action": "final", "answer": "Recovered."}',
        ])
        runner = ReactRunner(gateway=gw, max_steps=5)
        result = runner.run(goal="Test recovery", role="coder")
        assert result.success is True
        assert result.output == "Recovered."
        assert runner.step_history[0]["action"] == "parse_error"

    def test_max_steps_exceeded(self):
        responses = []
        for i in range(25):
            responses.append('{"action": "tool_call", "tool": "run_shell", "params": {"command": "echo loop"}}')
        gw = _MockGateway(responses)
        runner = ReactRunner(gateway=gw, max_steps=5)
        result = runner.run(goal="Infinite loop test", role="coder")
        assert result.success is False
        assert "maximum" in (result.error or "").lower()

    def test_tool_call_enforces_role(self):
        from tools.registry import ToolExecutor
        result = ToolExecutor.execute("web_search", {"query": "test"}, role="coder")
        assert result.success is False
        assert "not allowed" in (result.error or "").lower() or "cannot" in (result.error or "").lower()

    def test_tool_failure_does_not_crash_loop(self):
        gw = _MockGateway([
            '{"action": "tool_call", "tool": "read_file", "params": {"path": "/nonexistent/file.txt"}}',
            '{"action": "final", "answer": "Recovered from error."}',
        ])
        runner = ReactRunner(gateway=gw, max_steps=5)
        result = runner.run(goal="Test error recovery", role="researcher")
        assert result.success is True
        assert result.output == "Recovered from error."
        assert runner.step_history[0]["action"] == "tool_call"
        assert runner.step_history[0]["success"] is False

    def test_unknown_action_continues(self):
        gw = _MockGateway([
            '{"action": "dance", "style": "tango"}',
            '{"action": "final", "answer": "Done."}',
        ])
        runner = ReactRunner(gateway=gw, max_steps=5)
        result = runner.run(goal="Test unknown action", role="coder")
        assert result.success is True
        assert result.output == "Done."
        assert runner.step_history[0]["action"] == "unknown"

    def test_respects_max_steps_argument(self):
        gw = _MockGateway(['{"action": "final", "answer": "OK"}'] * 10)
        runner = ReactRunner(gateway=gw, max_steps=3)
        runner.run(goal="Quick task", role="coder")
        # Should complete in 1 step (immediate final), not hit max
        assert len(gw.calls) <= 2
