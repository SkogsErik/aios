"""
test_end_to_end_real.py — Real model end-to-end test.

Requires Ollama running with llama3.2:3b available.
Run: PYTHONPATH=platform/conductor/src:platform/model-gateway/src python3 -m pytest platform/conductor/tests/test_end_to_end_real.py -v -s
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "platform" / "conductor" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "platform" / "model-gateway" / "src"))

from conductor import Conductor
from session import SessionStore
from orchestrator import PlanStore
from task_store import TaskStore


@pytest.mark.skipif(
    not Path("/usr/bin/ollama").exists() and not Path("/usr/local/bin/ollama").exists(),
    reason="Ollama not installed",
)
class TestEndToEndReal:
    """Runs a real multi-role task against the actual model gateway.

    Tests are additive — each tests a larger slice of the pipeline.
    """

    def test_gateway_basic_completion(self):
        """Verify the real gateway returns a non-empty response."""
        from gateway import complete
        resp = complete(
            "Reply with exactly one word: hello",
            caller_id="conductor.e2e_test",
            max_tokens=10,
            temperature=0.0,
        )
        assert resp.content.strip(), f"Empty response from gateway: {resp}"
        print(f"\n[gateway] response: {resp.content.strip()}")

    def test_reactrunner_single_step(self, tmp_path):
        """Run ReactRunner with a real model — simple final answer."""
        from react import ReactRunner
        runner = ReactRunner(max_steps=5)
        result = runner.run(
            goal="Reply with exactly 'Hello from ReAct' and nothing else.",
            role="coder",
        )
        print(f"\n[react] success={result.success}, output={result.output[:200]}")
        assert result.success, f"ReAct failed: {result.error}"

    def test_tool_read_file_real(self, tmp_path):
        """Run a ReAct loop that uses read_file on a real file."""
        from react import ReactRunner
        from pathlib import Path
        _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        test_file = _REPO_ROOT / "platform" / "conductor" / "tests" / "_e2e_test_file.txt"
        test_file.write_text("Hello from the e2e test file!")
        try:
            runner = ReactRunner(max_steps=5)
            result = runner.run(
                goal=f"Read the file at {test_file} and tell me what it says.",
                role="researcher",
            )
            print(f"\n[read_file] success={result.success}, output={result.output[:300]}")
            print("[read_file] step history:")
            for s in runner.step_history:
                print(f"  step {s['step']}: action={s['action']}, tool={s.get('tool', '')}")
                print(f"    result: {str(s.get('result', ''))[:200]}")
            assert result.success, f"Read file task failed: {result.error}"
            assert "Hello from the e2e test" in result.output
        finally:
            test_file.unlink(missing_ok=True)

    def test_tool_write_file_real(self, tmp_path):
        """Run a ReAct loop using write_file to create a file."""
        from react import ReactRunner
        from pathlib import Path
        _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        target = _REPO_ROOT / "platform" / "conductor" / "tests" / "_e2e_output.txt"

        runner = ReactRunner(max_steps=5, model="ollama/qwen2.5:7b-instruct")
        result = runner.run(
            goal=f"Write a file at {target} containing the text 'E2E test passed!'",
            role="coder",
        )
        print(f"\n[write_file] success={result.success}, output={result.output[:300]}")
        print("[write_file] step history:")
        for s in runner.step_history:
            print(f"  step {s['step']}: action={s['action']}, tool={s.get('tool', '')}")
            print(f"    result: {str(s.get('result', ''))[:200]}")
        try:
            if result.success:
                content = target.read_text()
                print(f"  file content: {content}")
        finally:
            target.unlink(missing_ok=True)

    def test_decomposition_real(self, tmp_path):
        """Verify the model can decompose a simple goal into steps."""
        from orchestrator import PlanOrchestrator
        orch = PlanOrchestrator(max_steps=4)
        steps = orch.decompose("Write a Python script that prints Hello World and save it to a file.")
        print(f"\n[decomposition] {len(steps)} steps:")
        for s in steps:
            print(f"  {s['id']}: [{s['role']}] {s['goal']}")
        assert len(steps) >= 1
        for s in steps:
            assert s["role"] in ("researcher", "coder", "synthesizer")
            assert s["goal"]

    def test_coder_only_plan(self, tmp_path):
        """Two coder steps: write a script, then verify it exists — using explicit steps."""
        model = "ollama/qwen2.5:7b-instruct"
        from pathlib import Path
        _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        script_path = _REPO_ROOT / "platform" / "conductor" / "tests" / "_e2e_hello.py"

        task_store = TaskStore(base_dir=tmp_path / "tasks")
        steps = [
            {"id": "STP-001", "goal": f"Write a Python script at {script_path} that prints 'Hello from AIOS'", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
            {"id": "STP-002", "goal": f"Read the file at {script_path} to verify it was written correctly", "role": "coder", "status": "pending", "task_id": None, "result": None, "error": None},
        ]
        try:
            conductor = Conductor(
                session_store=SessionStore(base_dir=tmp_path / "sessions"),
                task_store=task_store,
                stores={},
                obs_dir=tmp_path / "observations",
                model=model,
            )

            plan = conductor.create_plan(
                "Write a Python script that prints 'Hello from AIOS'.",
                steps=steps,
            )
            print(f"\n[plan] {plan['id']}: {len(plan['steps'])} steps (model={model})")

            result = conductor.execute_plan(plan["id"])
            print(f"\n[execute] status={result['status']}")
            if result["status"] == "completed":
                print(f"  result: {result['result'][:500]}")
            else:
                print(f"  error: {result.get('error', 'unknown')}")

            loaded = conductor.get_plan(plan["id"])
            for s in loaded["steps"]:
                print(f"  step {s['id']}: status={s['status']}, task_id={s['task_id']}")
                if s.get("error"):
                    print(f"    error: {s['error']}")
        finally:
            script_path.unlink(missing_ok=True)

    def test_web_search_real(self):
        """Verify the researcher role can do a web search."""
        from react import ReactRunner
        runner = ReactRunner(max_steps=5, model="ollama/qwen2.5:7b-instruct")
        result = runner.run(
            goal="Search the web for 'Python programming language features' and summarize one feature.",
            role="researcher",
        )
        print(f"\n[web_search] success={result.success}, output={result.output[:300]}")
        print("[web_search] step history:")
        for s in runner.step_history:
            print(f"  step {s['step']}: action={s['action']}, tool={s.get('tool', '')}")
            res = str(s.get('result', ''))[:150]
            if res:
                print(f"    result: {res}")
        assert result.success, f"Web search task failed: {result.error}"

    def test_researcher_to_coder_orchestration(self, tmp_path):
        """Full multi-role orchestration: researcher web search → coder saves results to a file."""
        model = "ollama/qwen2.5:7b-instruct"
        output_path = _REPO_ROOT / "platform" / "conductor" / "tests" / "_e2e_research_output.txt"

        conductor = Conductor(
            session_store=SessionStore(base_dir=tmp_path / "sessions"),
            task_store=TaskStore(base_dir=tmp_path / "tasks"),
            stores={},
            obs_dir=tmp_path / "observations",
            model=model,
        )

        steps = [
            {
                "id": "STP-RES",
                "goal": "Search the web for 'Python programming language history' and summarize who created it and when.",
                "role": "researcher",
                "status": "pending", "task_id": None, "result": None, "error": None,
            },
            {
                "id": "STP-COD",
                "goal": f"Save a summary of Python's history to {output_path}. Content should mention Guido van Rossum and the year Python was first released.",
                "role": "coder",
                "status": "pending", "task_id": None, "result": None, "error": None,
            },
        ]

        try:
            plan = conductor.create_plan("Research Python history and save a summary.", steps=steps)
            print(f"\n[orchestration] plan {plan['id']}: {len(plan['steps'])} steps")

            result = conductor.execute_plan(plan["id"])
            print(f"\n[orchestration] status={result['status']}")
            if result.get("error"):
                print(f"  error: {result['error']}")

            loaded = conductor.get_plan(plan["id"])
            for s in loaded["steps"]:
                print(f"  step {s['id']}: status={s['status']}")
                if s.get("result"):
                    print(f"    result: {s['result'][:200]}")
                if s.get("error"):
                    print(f"    error: {s['error']}")

            assert result["status"] == "completed", f"Plan failed: {result.get('error')}"
            if output_path.exists():
                content = output_path.read_text()
                print(f"\n  output file content: {content[:200]}")
        finally:
            output_path.unlink(missing_ok=True)