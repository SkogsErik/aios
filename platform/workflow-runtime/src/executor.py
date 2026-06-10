"""
executor.py — Workflow executor

Reads a YAML workflow definition, resolves inputs, and executes steps
sequentially. Produces a YAML run record for every execution.

Capability: CAP-004 (Workflow Orchestration)
Defined by: ADR-005 — Workflow Engine Technology Selection
"""

import shlex
import subprocess
from pathlib import Path
from typing import Callable, Optional

import yaml

from run_log import (
    DEFAULT_RUNS_DIR,
    add_step_result,
    complete_run,
    new_run,
    save_run,
    _timestamp,
)
from validator import validate


class WorkflowError(Exception):
    """Raised when a workflow cannot be loaded or has a validation error."""


class StepFailedError(Exception):
    """Raised when a step exits with a non-zero code and allow_failure is False."""
    def __init__(self, step_id: str, exit_code: int):
        super().__init__(f"Step '{step_id}' failed with exit code {exit_code}.")
        self.step_id = step_id
        self.exit_code = exit_code


def load_definition(path: Path) -> dict:
    """Load and validate a workflow definition from a YAML file."""
    if not path.exists():
        raise WorkflowError(f"Workflow definition not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        definition = yaml.safe_load(f)
    errors = validate(definition)
    if errors:
        detail = "\n  ".join(errors)
        raise WorkflowError(f"Workflow definition is invalid:\n  {detail}")
    return definition


def _resolve_command(template: str, inputs: dict) -> str:
    """Substitute {var_name} placeholders with input values."""
    try:
        return template.format(**inputs)
    except KeyError as exc:
        raise WorkflowError(
            f"Command references undefined input variable: {exc}. "
            f"Available inputs: {list(inputs.keys())}"
        ) from exc


def run_workflow(
    definition_path: Path,
    inputs: Optional[dict] = None,
    *,
    approval_handler: Optional[Callable[[str, str], bool]] = None,
    runs_dir: Optional[Path] = None,
    cwd: Optional[Path] = None,
) -> dict:
    """
    Execute a workflow and return the run record.

    Parameters
    ----------
    definition_path : Path
        Path to the YAML workflow definition file.
    inputs : dict, optional
        Input variable values. Missing required inputs raise WorkflowError.
    approval_handler : callable, optional
        Called before any step with requires_approval=True. Signature:
        (step_id: str, step_name: str) -> bool (True = approved).
        If None, a CLI prompt is used.
    runs_dir : Path, optional
        Directory to write run records. Defaults to platform/workflow-runtime/runs/.
    cwd : Path, optional
        Working directory for step commands. Defaults to the repository root.

    Returns
    -------
    dict
        The completed run record.
    """
    definition = load_definition(definition_path)
    resolved_inputs = dict(inputs or {})

    # Validate required inputs
    for input_spec in definition.get("inputs", []):
        name = input_spec["name"]
        if input_spec.get("required", False) and name not in resolved_inputs:
            default = input_spec.get("default")
            if default is not None:
                resolved_inputs[name] = default
            else:
                raise WorkflowError(
                    f"Required input '{name}' was not provided."
                )

    run = new_run(definition, resolved_inputs, runs_dir=runs_dir)
    repo_root = Path(__file__).parent.parent.parent.parent
    working_dir = Path(cwd) if cwd else repo_root
    final_status = "success"

    for step in definition["steps"]:
        step_id = step["id"]
        step_name = step["name"]
        approval_required = step.get("requires_approval", False)
        allow_failure = step.get("allow_failure", False)
        command_template = step["command"]
        approved_by: Optional[str] = None

        # Human approval gate
        if approval_required:
            if approval_handler is not None:
                approved = approval_handler(step_id, step_name)
            else:
                approved = _cli_approval_prompt(step_id, step_name)
            if not approved:
                complete_run(run, "aborted")
                save_run(run, runs_dir=runs_dir)
                raise WorkflowError(
                    f"Workflow aborted: operator declined approval for step '{step_id}'."
                )
            approved_by = "operator"

        command = _resolve_command(command_template, resolved_inputs)
        step_started = _timestamp()

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(working_dir),
        )

        step_completed = _timestamp()

        add_step_result(
            run,
            step_id=step_id,
            step_name=step_name,
            started_at=step_started,
            completed_at=step_completed,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            approval_required=approval_required,
            approved_by=approved_by,
        )

        if result.returncode != 0 and not allow_failure:
            complete_run(run, "failed")
            save_run(run, runs_dir=runs_dir)
            raise StepFailedError(step_id, result.returncode)

    complete_run(run, final_status)
    save_run(run, runs_dir=runs_dir)
    return run


def _cli_approval_prompt(step_id: str, step_name: str) -> bool:
    """Interactive CLI prompt for human approval."""
    print(f"\n[APPROVAL REQUIRED] Step '{step_id}': {step_name}")
    answer = input("Approve? [y/N] ").strip().lower()
    return answer in ("y", "yes")
