from __future__ import annotations

import datetime
import re
import shutil
from pathlib import Path
from typing import Any, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TASKS_DIR = _REPO_ROOT / "platform" / "knowledge" / "tasks"

_TSK_PATTERN = re.compile(r"^TSK-(\d{4}-\d{4})-(\d+)$")


def make_task(
    task_id: str,
    goal: str,
    role: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "id": task_id,
        "goal": goal,
        "role": role,
        "session_id": session_id,
        "status": "pending",
        "created": now,
        "updated": now,
        "steps": [],
        "result": None,
    }


def make_step(
    action: str,
    tool_name: str | None = None,
    tool_params: dict[str, Any] | None = None,
    observation: str | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "tool_name": tool_name,
        "tool_params": tool_params,
        "observation": observation,
    }


class TaskStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._dir = (base_dir or _TASKS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, task_id: str) -> Path:
        return self._dir / f"{task_id}.yaml"

    def next_id(self, when: datetime.date | None = None) -> str:
        date = when or datetime.date.today()
        prefix = date.strftime("%Y-%m%d")
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob(f"TSK-{prefix}-*.yaml"):
                m = _TSK_PATTERN.match(f.stem)
                if m and m.group(1) == prefix:
                    max_n = max(max_n, int(m.group(2)))
        return f"TSK-{prefix}-{max_n + 1:03d}"

    def create(
        self,
        goal: str,
        role: str,
        session_id: str | None = None,
        when: datetime.date | None = None,
    ) -> dict[str, Any]:
        task_id = self.next_id(when=when)
        task = make_task(task_id, goal, role, session_id=session_id)
        self.save(task)
        return self.get(task_id)

    def save(self, task: dict[str, Any]) -> None:
        self._ensure_dir()
        data = dict(task)
        data["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        path = self._path_for(task["id"])
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def get(self, task_id: str) -> dict[str, Any] | None:
        path = self._path_for(task_id)
        if not path.exists():
            return None
        with open(path) as f:
            return yaml.safe_load(f)

    def list_all(self) -> list[dict[str, Any]]:
        if not self._dir.exists():
            return []
        tasks = []
        for path in sorted(self._dir.glob("TSK-*.yaml")):
            with open(path) as f:
                tasks.append(yaml.safe_load(f))
        return tasks

    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        return [t for t in self.list_all() if t.get("status") == status]

    def add_step(self, task_id: str, step: dict[str, Any]) -> dict[str, Any] | None:
        task = self.get(task_id)
        if task is None:
            return None
        task["steps"] = list(task.get("steps") or []) + [step]
        self.save(task)
        return self.get(task_id)

    def update_status(self, task_id: str, status: str) -> dict[str, Any] | None:
        task = self.get(task_id)
        if task is None:
            return None
        task["status"] = status
        self.save(task)
        return self.get(task_id)

    def set_result(self, task_id: str, result: str) -> dict[str, Any] | None:
        task = self.get(task_id)
        if task is None:
            return None
        task["result"] = result
        self.save(task)
        return self.get(task_id)
