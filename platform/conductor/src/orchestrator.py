from __future__ import annotations

import datetime
import json
import re
import shutil
from pathlib import Path
from typing import Any, Callable

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_GATEWAY_SRC = _REPO_ROOT / "platform" / "model-gateway" / "src"
if str(_GATEWAY_SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_GATEWAY_SRC))

_PLANS_DIR = _REPO_ROOT / "platform" / "knowledge" / "plans"
_PLN_PATTERN = re.compile(r"^PLN-(\d{4}-\d{4})-(\d+)$")

DECOMPOSITION_PROMPT = """\
You are a planning agent. Decompose the following operator goal into a sequence of steps.

Each step must be assigned to exactly one of these agent roles:

- researcher: can read files and search the web. Use for information gathering, fact-finding, exploring existing code, looking up documentation.
- coder: can read files, write files, and run shell commands. Use for writing code, creating scripts, running tests, executing commands, building things.
- synthesizer: can only read files. Use for analysing results, summarising findings, producing structured reports from data gathered by earlier steps.

Rules:
1. Every step must have exactly one role.
2. Steps must be ordered — later steps can depend on earlier steps.
3. Each step's goal must be self-contained and actionable using only the tools available to that role.
4. Keep goals detailed and specific — not vague.
5. Produce 1-6 steps maximum. Fewer is better.

Operator goal: {goal}

Respond with ONLY a JSON object in this exact format — no other text:
{{
  "steps": [
    {{"goal": "Detailed description of step 1", "role": "researcher"}},
    {{"goal": "Detailed description of step 2", "role": "coder"}}
  ]
}}
"""


def _find_json_object(text: str) -> str | None:
    text = text.strip()
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


class PlanStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._dir = (base_dir or _PLANS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, plan_id: str) -> Path:
        return self._dir / f"{plan_id}.yaml"

    def next_id(self, when: datetime.date | None = None) -> str:
        date = when or datetime.date.today()
        prefix = date.strftime("%Y-%m%d")
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob(f"PLN-{prefix}-*.yaml"):
                m = _PLN_PATTERN.match(f.stem)
                if m and m.group(1) == prefix:
                    max_n = max(max_n, int(m.group(2)))
        return f"PLN-{prefix}-{max_n + 1:03d}"

    def save(self, plan: dict[str, Any]) -> None:
        self._ensure_dir()
        data = dict(plan)
        data["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        path = self._path_for(plan["id"])
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def get(self, plan_id: str) -> dict[str, Any] | None:
        path = self._path_for(plan_id)
        if not path.exists():
            return None
        with open(path) as f:
            return yaml.safe_load(f)

    def list_all(self) -> list[dict[str, Any]]:
        if not self._dir.exists():
            return []
        plans = []
        for path in sorted(self._dir.glob("PLN-*.yaml")):
            with open(path) as f:
                plans.append(yaml.safe_load(f))
        return plans


def _make_plan(
    plan_id: str,
    goal: str,
    steps: list[dict[str, Any]],
    session_id: str | None = None,
) -> dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "id": plan_id,
        "goal": goal,
        "session_id": session_id,
        "status": "pending",
        "created": now,
        "updated": now,
        "steps": steps,
        "result": None,
    }


def _make_step_from_decomposition(
    step_num: int,
    goal: str,
    role: str,
) -> dict[str, Any]:
    return {
        "id": f"STP-{step_num:03d}",
        "goal": goal,
        "role": role,
        "status": "pending",
        "task_id": None,
        "result": None,
        "error": None,
    }


class PlanOrchestrator:
    def __init__(
        self,
        gateway=None,
        plan_store: PlanStore | None = None,
        confirmation_gate: Callable[[str, str], bool] | None = None,
        max_steps: int = 6,
        model: str | None = None,
    ) -> None:
        if gateway is None:
            from gateway import complete as _complete
            self._complete = _complete
        else:
            self._complete = gateway.complete
        self._plan_store = plan_store or PlanStore()
        self._confirmation_gate = confirmation_gate
        self._max_steps = max_steps
        self._model = model

    def decompose(self, goal: str) -> list[dict[str, Any]]:
        prompt = DECOMPOSITION_PROMPT.format(goal=goal)
        response = self._complete(
            prompt,
            caller_id="conductor.orchestrator",
            max_tokens=2000,
            temperature=0.0,
            context={"purpose": "goal_decomposition"},
            model=self._model,
        )
        raw = response.content.strip()

        parsed = self._parse_decomposition(raw)
        if parsed is None:
            return [{"goal": goal, "role": "coder"}]

        steps = []
        for i, step in enumerate(parsed):
            role = step.get("role", "coder")
            if role not in ("researcher", "coder", "synthesizer"):
                role = "coder"
            steps.append(_make_step_from_decomposition(i + 1, step["goal"], role))
        return steps[: self._max_steps]

    def create_plan(
        self,
        goal: str,
        steps: list[dict[str, Any]] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if steps is None:
            steps = self.decompose(goal)
        plan_id = self._plan_store.next_id()
        plan = _make_plan(plan_id, goal, steps, session_id=session_id)
        self._plan_store.save(plan)
        return dict(plan)

    def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        return self._plan_store.get(plan_id)

    def list_plans(self) -> list[dict[str, Any]]:
        return self._plan_store.list_all()

    def execute_plan(
        self,
        plan_id: str,
        conductor: Any,
        confirmation_gate: Callable[[str, str], bool] | None = None,
    ) -> dict[str, Any]:
        plan = self._plan_store.get(plan_id)
        if plan is None:
            return {"error": f"Plan {plan_id} not found"}

        if plan["status"] != "pending":
            return {"error": f"Plan {plan_id} is already {plan['status']}"}

        plan["status"] = "in_progress"
        self._plan_store.save(plan)

        gate = confirmation_gate or self._confirmation_gate
        accumulated_context = ""

        for step in plan["steps"]:
            if step["status"] == "completed":
                accumulated_context = self._build_prior_results(plan["steps"])
                continue

            if gate is not None:
                ok = gate(step["id"], step["goal"])
                if not ok:
                    step["status"] = "blocked"
                    step["error"] = "Operator declined to execute this step"
                    plan["status"] = "blocked"
                    self._plan_store.save(plan)
                    return {
                        "plan_id": plan_id,
                        "status": "blocked",
                        "blocked_step": step["id"],
                        "error": f"Operator blocked step {step['id']}: {step['goal']}",
                    }

            step["status"] = "in_progress"
            self._plan_store.save(plan)

            result = conductor.run_task(
                goal=step["goal"],
                role=step["role"],
                session_id=plan.get("session_id"),
                prior_results=accumulated_context,
                model=self._model,
            )

            if result["status"] == "completed":
                step["status"] = "completed"
                step["task_id"] = result["task_id"]
                step["result"] = result["result"]
                accumulated_context = self._build_prior_results(plan["steps"])
            else:
                step["status"] = "failed"
                step["task_id"] = result["task_id"]
                step["error"] = result.get("error", "Unknown error")
                plan["status"] = "blocked"
                self._plan_store.save(plan)
                return {
                    "plan_id": plan_id,
                    "status": "blocked",
                    "blocked_step": step["id"],
                    "error": f"Step {step['id']} failed: {step.get('error', 'Unknown error')}",
                    "partial_results": [
                        {"step": s["id"], "result": s["result"]}
                        for s in plan["steps"]
                        if s["status"] == "completed"
                    ],
                }

        plan["status"] = "completed"
        plan["result"] = self._accumulate_results(plan["steps"])
        self._plan_store.save(plan)

        return {
            "plan_id": plan_id,
            "status": "completed",
            "result": plan["result"],
            "step_count": len(plan["steps"]),
        }

    def _build_prior_results(self, steps: list[dict[str, Any]]) -> str:
        parts = []
        for s in steps:
            if s.get("result"):
                parts.append(
                    f"=== Step {s['id']}: {s['goal']} ===\n{s['result']}"
                )
        return "\n\n".join(parts)

    def _accumulate_results(self, steps: list[dict[str, Any]]) -> str:
        parts = []
        for s in steps:
            if s.get("result"):
                parts.append(f"Step {s['id']} ({s['goal']}):\n{s['result']}")
        return "\n\n---\n\n".join(parts)

    def _parse_decomposition(self, raw: str) -> list[dict[str, Any]] | None:
        obj = _find_json_object(raw)
        if obj is None:
            return None
        try:
            data = json.loads(obj)
        except (json.JSONDecodeError, TypeError):
            return None
        steps = data.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            return None
        for s in steps:
            if not isinstance(s, dict) or "goal" not in s or "role" not in s:
                return None
        return steps
