from pathlib import Path

import pytest

from conductor import Conductor
from session import SessionStore
from task_store import TaskStore
from react import ReactRunner


class _MockResponse:
    def __init__(self, content: str):
        self.content = content


class _MockGateway:
    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or []
        self._index = 0
        self.calls = []

    def complete(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt[:50], **kwargs})
        if self._index < len(self._responses):
            resp = self._responses[self._index]
            self._index += 1
            return _MockResponse(resp)
        return _MockResponse('{"action": "final", "answer": "Done."}')


class TestConductorRunTask:
    def test_run_task_immediate_final(self, tmp_path):
        gw = _MockGateway(['{"action": "final", "answer": "Task complete."}'])
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            gateway=gw,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        result = conductor.run_task(goal="Say hello", role="coder")
        assert result["status"] == "completed"
        assert result["result"] == "Task complete."
        assert result["step_count"] >= 1
        assert result["task"]["id"].startswith("TSK-")

    def test_run_task_failure(self, tmp_path):
        """When ReAct loop exceeds max steps, task should be marked failed."""
        responses = ['{"action": "tool_call", "tool": "read_file", "params": {"path": "/nope"}}'] * 25
        gw = _MockGateway(responses)
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            gateway=gw,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        result = conductor.run_task(goal="Loop test", role="researcher")
        assert result["status"] == "failed"
        assert result["error"] is not None

    def test_run_task_persists_to_task_store(self, tmp_path):
        task_store = TaskStore(base_dir=tmp_path / "tasks")
        gw = _MockGateway(['{"action": "final", "answer": "Persisted."}'])
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            task_store=task_store,
            gateway=gw,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        result = conductor.run_task(goal="Persistence test", role="coder")
        task = task_store.get(result["task_id"])
        assert task is not None
        assert task["status"] == "completed"
        assert task["result"] == "Persisted."

    def test_run_task_with_session_id(self, tmp_path):
        gw = _MockGateway(['{"action": "final", "answer": "Linked to session."}'])
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            gateway=gw,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        result = conductor.run_task(
            goal="Session test",
            role="coder",
            session_id="SES-2026-0612-001",
        )
        assert result["task"]["session_id"] == "SES-2026-0612-001"

    def test_run_task_records_steps(self, tmp_path):
        gw = _MockGateway([
            '{"action": "tool_call", "tool": "read_file", "params": {"path": "' + __file__.replace("\\", "\\\\") + '"}}',
            '{"action": "final", "answer": "Read file and done."}',
        ])
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            gateway=gw,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        result = conductor.run_task(goal="Read and respond", role="researcher")
        assert result["step_count"] == 2
        assert result["status"] == "completed"


class TestConductorConfirmationGate:
    def test_confirmation_gate_blocks_plan_execution(self, tmp_path):
        def gate(step_id: str, goal: str) -> bool:
            return False

        gw = _MockGateway([
            '{"steps": [{"goal": "Research", "role": "researcher"}, {"goal": "Build", "role": "coder"}]}',
            '{"action": "final", "answer": "Done."}',
        ])
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            gateway=gw,
            confirmation_gate=gate,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        plan = conductor.create_plan("Build something")
        result = conductor.execute_plan(plan["id"])
        assert result["status"] == "blocked"

    def test_confirmation_gate_allows_execution(self, tmp_path):
        def gate(step_id: str, goal: str) -> bool:
            return True

        gw = _MockGateway([
            '{"steps": [{"goal": "Research", "role": "researcher"}]}',
            '{"action": "final", "answer": "Done."}',
        ])
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            gateway=gw,
            confirmation_gate=gate,
            stores={},
            obs_dir=tmp_path / "observations",
        )
        plan = conductor.create_plan("Build something")
        result = conductor.execute_plan(plan["id"])
        assert result["status"] == "completed"


class TestConductorOrchestrationSmoke:
    """End-to-end smoke test: create_plan → execute_plan → steps persisted."""

    def test_full_orchestration_pipeline(self, tmp_path):
        gw = _MockGateway([
            # Decomposition call (create_plan)
            '{"steps": [{"goal": "Research Python libraries", "role": "researcher"}, {"goal": "Write hello script", "role": "coder"}]}',
            # ReactRunner for step 1 (researcher)
            '{"action": "final", "answer": "Found: requests and httpx."}',
            # ReactRunner for step 2 (coder)
            '{"action": "final", "answer": "Script written successfully."}',
        ])
        task_store = TaskStore(base_dir=tmp_path / "tasks")
        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            task_store=task_store,
            gateway=gw,
            stores={},
            obs_dir=tmp_path / "observations",
        )

        plan = conductor.create_plan("Build a Python scraper script")
        plan_id = plan["id"]
        assert plan["status"] == "pending"
        assert len(plan["steps"]) == 2
        assert plan["steps"][0]["role"] == "researcher"
        assert plan["steps"][1]["role"] == "coder"

        result = conductor.execute_plan(plan_id)
        assert result["status"] == "completed"
        assert result["step_count"] == 2

        loaded_plan = conductor.get_plan(plan_id)
        assert loaded_plan["status"] == "completed"

        for step in loaded_plan["steps"]:
            assert step["status"] == "completed"
            assert step["task_id"] is not None
            task = task_store.get(step["task_id"])
            assert task is not None
            assert task["status"] == "completed"
            assert task["role"] == step["role"]
