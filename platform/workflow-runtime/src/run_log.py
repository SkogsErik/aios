"""
run_log.py — Workflow run record writer

Every workflow execution produces a YAML run record in the configured
runs directory. Run records are the primary audit artefact for workflow
execution as required by Phase 4 deliverables and ADR-005.

Capability: CAP-004 (Workflow Orchestration)
Defined by: ADR-005 — Workflow Engine Technology Selection
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

DEFAULT_RUNS_DIR = Path(__file__).parent.parent / "runs"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_filename(workflow_id: str, runs_dir: Optional[Path] = None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = f"{workflow_id}-run-{ts}"
    name = f"{base}.yaml"
    if runs_dir:
        counter = 1
        while (runs_dir / name).exists():
            name = f"{base}-{counter}.yaml"
            counter += 1
    return name


def new_run(
    workflow: dict,
    inputs: dict,
    runs_dir: Optional[Path] = None,
) -> dict:
    """
    Initialise a run record for a workflow execution.

    The run_id is a placeholder until save_run() assigns the final file-safe
    ID (collision-free). Callers should not depend on run_id before save_run()
    is called.
    """
    return {
        "run_id": None,  # finalised by save_run()
        "workflow_id": workflow["id"],
        "workflow_title": workflow.get("title", ""),
        "workflow_version": workflow.get("version", 1),
        "started_at": _timestamp(),
        "completed_at": None,
        "status": "running",
        "inputs": inputs,
        "steps": [],
    }


def add_step_result(
    run: dict,
    *,
    step_id: str,
    step_name: str,
    started_at: str,
    completed_at: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    approval_required: bool,
    approved_by: Optional[str],
) -> None:
    """Append a completed step result to the run record."""
    status = "success" if exit_code == 0 else "failed"
    run["steps"].append({
        "id": step_id,
        "name": step_name,
        "started_at": started_at,
        "completed_at": completed_at,
        "exit_code": exit_code,
        "status": status,
        "stdout": stdout.strip() if stdout else "",
        "stderr": stderr.strip() if stderr else "",
        "approval_required": approval_required,
        "approved_by": approved_by,
    })


def complete_run(run: dict, status: str) -> None:
    """Mark the run as complete with the given status."""
    run["completed_at"] = _timestamp()
    run["status"] = status


def save_run(run: dict, runs_dir: Optional[Path] = None) -> Path:
    """
    Write the run record to disk.

    Assigns run_id at save time to guarantee a collision-free filename even
    when multiple runs are created within the same second.
    Returns the path to the written file.
    """
    dir_ = Path(runs_dir) if runs_dir else DEFAULT_RUNS_DIR
    dir_.mkdir(parents=True, exist_ok=True)
    filename = _run_filename(run["workflow_id"], runs_dir=dir_)
    run["run_id"] = filename.replace(".yaml", "")
    path = dir_ / filename
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(run, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return path


def load_run(path: Path) -> dict:
    """Load a run record from disk."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_runs(runs_dir: Optional[Path] = None) -> list[Path]:
    """Return all run record files, sorted newest first."""
    dir_ = Path(runs_dir) if runs_dir else DEFAULT_RUNS_DIR
    if not dir_.exists():
        return []
    return sorted(dir_.glob("*.yaml"), reverse=True)
