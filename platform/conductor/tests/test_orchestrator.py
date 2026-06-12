import datetime
from pathlib import Path

import pytest

from orchestrator import PlanOrchestrator, PlanStore, _find_json_object


class _MockResponse:
    def __init__(self, content: str):
        self.content = content


class _MockGateway:
    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or []
        self._index = 0
        self.calls = []

    def complete(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt[:80], **kwargs})
        if self._index < len(self._responses):
            resp = self._responses[self._index]
            self._index += 1
            return _MockResponse(resp)
        return _MockResponse('{"action": "final", "answer": "Done."}')


class _MockConductor:
    def __init__(self, results: list[dict] | None = None):
        self._results = results or []
        self._index = 0
        self.calls = []

    def run_task(self, goal: str, role: str, session_id: str | None = None):
        self.calls.append({"goal": goal, "role": role, "session_id": session_id})
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            return result
        return {
            "task_id": "TSK-2026-0612-001",
            "status": "completed",
            "result": f"Done: {goal[:30]}",
            "error": None,
            "step_count": 1,
            "task": {"id": "TSK-2026-0612-001", "status": "completed", "result": f"Done: {goal[:30]}", "steps": []},
        }


# ---------------------------------------------------------------------------
# PlanStore
# ---------------------------------------------------------------------------


class TestPlanStoreNextId:
    def test_first_id_format(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        today = datetime.date(2026, 6, 12)
        sid = store.next_id(when=today)
        assert sid == "PLN-2026-0612-001"

    def test_increments_same_day(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        today = datetime.date(2026, 6, 12)
        store.save({"id": store.next_id(when=today), "goal": "Test", "steps": []})
        assert store.next_id(when=today) == "PLN-2026-0612-002"

    def test_independent_across_days(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        store.save({"id": store.next_id(when=datetime.date(2026, 6, 10)), "goal": "Old", "steps": []})
        assert store.next_id(when=datetime.date(2026, 6, 12)) == "PLN-2026-0612-001"


class TestPlanStoreSaveGet:
    def test_save_and_get(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        plan = {
            "id": "PLN-2026-0612-001",
            "goal": "Test goal",
            "status": "pending",
            "steps": [],
        }
        store.save(plan)
        loaded = store.get("PLN-2026-0612-001")
        assert loaded is not None
        assert loaded["goal"] == "Test goal"
        assert loaded["status"] == "pending"

    def test_get_not_found(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        assert store.get("PLN-2026-0612-999") is None

    def test_list_all(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        store.save({"id": "PLN-2026-0612-001", "goal": "Plan A", "steps": []})
        store.save({"id": "PLN-2026-0612-002", "goal": "Plan B", "steps": []})
        plans = store.list_all()
        assert len(plans) == 2


# ---------------------------------------------------------------------------
# PlanOrchestrator — Decomposition
# ---------------------------------------------------------------------------


class TestPlanOrchestratorDecompose:
    def test_decomposes_goal_into_steps(self):
        gw = _MockGateway([
            '{"steps": [{"goal": "Research libraries", "role": "researcher"}, {"goal": "Write code", "role": "coder"}]}',
        ])
        orch = PlanOrchestrator(gateway=gw)
        steps = orch.decompose("Build a scraper")
        assert len(steps) == 2
        assert steps[0]["goal"] == "Research libraries"
        assert steps[0]["role"] == "researcher"
        assert steps[0]["id"] == "STP-001"
        assert steps[1]["goal"] == "Write code"
        assert steps[1]["role"] == "coder"
        assert steps[1]["id"] == "STP-002"

    def test_fallback_on_parse_failure(self):
        gw = _MockGateway(["not json at all"])
        orch = PlanOrchestrator(gateway=gw)
        steps = orch.decompose("Do something")
        assert len(steps) == 1
        assert steps[0]["goal"] == "Do something"
        assert steps[0]["role"] == "coder"

    def test_fallback_on_empty_steps(self):
        gw = _MockGateway(['{"steps": []}'])
        orch = PlanOrchestrator(gateway=gw)
        steps = orch.decompose("Do something")
        assert len(steps) == 1
        assert steps[0]["role"] == "coder"

    def test_clamps_unknown_role_to_coder(self):
        gw = _MockGateway([
            '{"steps": [{"goal": "Do thing", "role": "analyst"}]}',
        ])
        orch = PlanOrchestrator(gateway=gw)
        steps = orch.decompose("Do something")
        assert steps[0]["role"] == "coder"

    def test_accepts_all_valid_roles(self):
        gw = _MockGateway([
            '{"steps": [{"goal": "Research", "role": "researcher"}, {"goal": "Code", "role": "coder"}, {"goal": "Synthesize", "role": "synthesizer"}]}',
        ])
        orch = PlanOrchestrator(gateway=gw)
        steps = orch.decompose("Do everything")
        assert len(steps) == 3
        assert steps[0]["role"] == "researcher"
        assert steps[1]["role"] == "coder"
        assert steps[2]["role"] == "synthesizer"

    def test_respects_max_steps(self):
        steps_list = [{"goal": f"Step {i}", "role": "coder"} for i in range(10)]
        gw = _MockGateway([json.dumps({"steps": steps_list})])
        orch = PlanOrchestrator(gateway=gw, max_steps=3)
        steps = orch.decompose("Do many things")
        assert len(steps) == 3


# ---------------------------------------------------------------------------
# PlanOrchestrator — create_plan
# ---------------------------------------------------------------------------


class TestPlanOrchestratorCreatePlan:
    def test_creates_plan_with_steps(self, tmp_path):
        orch = PlanOrchestrator(
            plan_store=PlanStore(base_dir=tmp_path),
        )
        steps = [
            {"id": "STP-001", "goal": "Research", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None},
            {"id": "STP-002", "goal": "Build", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
        ]
        plan = orch.create_plan("Build a scraper", steps=steps)
        assert plan["id"].startswith("PLN-")
        assert plan["goal"] == "Build a scraper"
        assert plan["status"] == "pending"
        assert len(plan["steps"]) == 2
        assert plan["steps"][0]["goal"] == "Research"

    def test_creates_plan_with_decomposition(self, tmp_path):
        gw = _MockGateway([
            '{"steps": [{"goal": "Research", "role": "researcher"}, {"goal": "Build", "role": "coder"}]}',
        ])
        orch = PlanOrchestrator(gateway=gw, plan_store=PlanStore(base_dir=tmp_path))
        plan = orch.create_plan("Build a scraper")
        assert plan["id"].startswith("PLN-")
        assert len(plan["steps"]) == 2

    def test_plan_is_persisted(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [{"id": "STP-001", "goal": "Research", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None}]
        plan = orch.create_plan("Test", steps=steps)
        loaded = store.get(plan["id"])
        assert loaded is not None
        assert loaded["goal"] == "Test"


# ---------------------------------------------------------------------------
# PlanOrchestrator — execute_plan
# ---------------------------------------------------------------------------


class TestPlanOrchestratorExecutePlan:
    def test_executes_all_steps_successfully(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [
            {"id": "STP-001", "goal": "Research topic", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None},
            {"id": "STP-002", "goal": "Write code", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
        ]
        plan = orch.create_plan("Build feature", steps=steps)
        mock = _MockConductor()
        result = orch.execute_plan(plan["id"], mock)
        assert result["status"] == "completed"
        assert result["step_count"] == 2
        assert len(mock.calls) == 2
        assert mock.calls[0]["goal"] == "Research topic"
        assert mock.calls[0]["role"] == "researcher"
        assert mock.calls[1]["goal"] == "Write code"
        assert mock.calls[1]["role"] == "coder"

    def test_stops_on_step_failure(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [
            {"id": "STP-001", "goal": "Research topic", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None},
            {"id": "STP-002", "goal": "Write code", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
        ]
        plan = orch.create_plan("Build feature", steps=steps)
        mock = _MockConductor(results=[
            {"task_id": "TSK-001", "status": "failed", "result": "", "error": "No data found", "step_count": 3, "task": {"id": "TSK-001", "status": "failed", "result": "", "steps": []}},
        ])
        result = orch.execute_plan(plan["id"], mock)
        assert result["status"] == "blocked"
        assert result["blocked_step"] == "STP-001"
        assert "failed" in result["error"] or "blocked" in result["error"]

    def test_plan_not_found(self, tmp_path):
        orch = PlanOrchestrator(plan_store=PlanStore(base_dir=tmp_path))
        result = orch.execute_plan("PLN-2026-0612-999", None)
        assert "error" in result
        assert "not found" in result["error"]

    def test_plan_already_executed(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [{"id": "STP-001", "goal": "Research", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None}]
        plan = orch.create_plan("Test", steps=steps)
        plan["status"] = "completed"
        store.save(plan)
        result = orch.execute_plan(plan["id"], _MockConductor())
        assert "error" in result
        assert "already" in result["error"]

    def test_confirmation_gate_blocks_step(self, tmp_path):
        def gate(step_id: str, goal: str) -> bool:
            return False  # block everything
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [{"id": "STP-001", "goal": "Research", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None}]
        plan = orch.create_plan("Test", steps=steps)
        result = orch.execute_plan(plan["id"], _MockConductor(), confirmation_gate=gate)
        assert result["status"] == "blocked"

    def test_accumulates_results(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [
            {"id": "STP-001", "goal": "Research", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None},
            {"id": "STP-002", "goal": "Build", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
        ]
        plan = orch.create_plan("Feature", steps=steps)
        mock = _MockConductor()
        result = orch.execute_plan(plan["id"], mock)
        assert result["status"] == "completed"
        assert "Research" in result["result"]
        assert "Build" in result["result"]

    def test_passes_session_id(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [{"id": "STP-001", "goal": "Research", "role": "researcher", "status": "pending", "task_id": None, "result": None, "error": None}]
        plan = orch.create_plan("Test", steps=steps, session_id="SES-001")
        mock = _MockConductor()
        orch.execute_plan(plan["id"], mock)
        assert mock.calls[0]["session_id"] == "SES-001"

    def test_skips_completed_steps(self, tmp_path):
        store = PlanStore(base_dir=tmp_path)
        orch = PlanOrchestrator(plan_store=store)
        steps = [
            {"id": "STP-001", "goal": "Research", "role": "researcher", "status": "completed", "task_id": "TSK-001", "result": "Done", "error": None},
            {"id": "STP-002", "goal": "Build", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
        ]
        plan = orch.create_plan("Feature", steps=steps)
        mock = _MockConductor()
        result = orch.execute_plan(plan["id"], mock)
        assert result["status"] == "completed"
        assert len(mock.calls) == 1
        assert mock.calls[0]["goal"] == "Build"


# ---------------------------------------------------------------------------
# _find_json_object
# ---------------------------------------------------------------------------


def test_find_json_object_nested():
    text = 'prefix {"a": {"b": "c"}} suffix'
    result = _find_json_object(text)
    assert result == '{"a": {"b": "c"}}'


def test_find_json_object_no_braces():
    assert _find_json_object("no json here") is None


def test_find_json_object_unbalanced():
    assert _find_json_object('{"a": "b"') is None


# Need json import for test_respects_max_steps
import json  # noqa: E402
