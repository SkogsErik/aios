"""
test_executor.py — Tests for the workflow executor.

Covers: successful execution, run record creation, step output capture,
approval gates, step failure handling, input validation, validation errors.
"""

import pytest
import yaml

import executor as exec_mod
import run_log as run_log_mod
import validator as validator_mod


# ---------------------------------------------------------------------------
# Successful execution
# ---------------------------------------------------------------------------

def test_run_simple_workflow_succeeds(simple_workflow, runs_dir):
    run = exec_mod.run_workflow(
        simple_workflow,
        inputs={"message": "hello"},
        runs_dir=runs_dir,
    )
    assert run["status"] == "success"
    assert run["workflow_id"] == "WF-001"


def test_run_records_step_output(simple_workflow, runs_dir):
    run = exec_mod.run_workflow(
        simple_workflow,
        inputs={"message": "hello"},
        runs_dir=runs_dir,
    )
    step = run["steps"][0]
    assert step["status"] == "success"
    assert step["exit_code"] == 0
    assert "hello" in step["stdout"]


def test_run_two_step_workflow(two_step_workflow, runs_dir):
    run = exec_mod.run_workflow(two_step_workflow, runs_dir=runs_dir)
    assert run["status"] == "success"
    assert len(run["steps"]) == 2
    assert run["steps"][0]["id"] == "step-1"
    assert run["steps"][1]["id"] == "step-2"


def test_run_writes_run_record_to_disk(simple_workflow, runs_dir):
    run = exec_mod.run_workflow(
        simple_workflow,
        inputs={"message": "test"},
        runs_dir=runs_dir,
    )
    saved_paths = run_log_mod.list_runs(runs_dir)
    assert len(saved_paths) == 1
    loaded = run_log_mod.load_run(saved_paths[0])
    assert loaded["workflow_id"] == "WF-001"
    assert loaded["status"] == "success"


def test_run_records_timestamps(simple_workflow, runs_dir):
    run = exec_mod.run_workflow(
        simple_workflow,
        inputs={"message": "hi"},
        runs_dir=runs_dir,
    )
    assert run["started_at"] is not None
    assert run["completed_at"] is not None
    assert run["steps"][0]["started_at"] is not None
    assert run["steps"][0]["completed_at"] is not None


def test_run_records_inputs(simple_workflow, runs_dir):
    run = exec_mod.run_workflow(
        simple_workflow,
        inputs={"message": "captured"},
        runs_dir=runs_dir,
    )
    assert run["inputs"]["message"] == "captured"


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------

def test_run_raises_for_missing_required_input(simple_workflow, runs_dir):
    with pytest.raises(exec_mod.WorkflowError, match="Required input"):
        exec_mod.run_workflow(simple_workflow, inputs={}, runs_dir=runs_dir)


def test_run_raises_for_undefined_command_variable(tmp_path, runs_dir):
    import yaml
    defn = {
        "id": "WF-005",
        "title": "Bad var workflow",
        "version": 1,
        "capability": "CAP-001",
        "steps": [{"id": "s1", "name": "Bad", "command": "echo {undefined_var}"}],
    }
    path = tmp_path / "WF-005.yaml"
    path.write_text(yaml.dump(defn))
    with pytest.raises(exec_mod.WorkflowError, match="undefined input variable"):
        exec_mod.run_workflow(path, inputs={}, runs_dir=runs_dir)


# ---------------------------------------------------------------------------
# Step failure
# ---------------------------------------------------------------------------

def test_run_fails_on_step_nonzero_exit(failing_workflow, runs_dir):
    with pytest.raises(exec_mod.StepFailedError) as exc_info:
        exec_mod.run_workflow(failing_workflow, runs_dir=runs_dir)
    assert exc_info.value.step_id == "step-1"
    assert exc_info.value.exit_code != 0


def test_run_records_failed_status_on_step_failure(failing_workflow, runs_dir):
    with pytest.raises(exec_mod.StepFailedError):
        exec_mod.run_workflow(failing_workflow, runs_dir=runs_dir)
    saved = run_log_mod.list_runs(runs_dir)
    run = run_log_mod.load_run(saved[0])
    assert run["status"] == "failed"
    assert run["steps"][0]["status"] == "failed"


def test_run_allow_failure_continues(tmp_path, runs_dir):
    defn = {
        "id": "WF-006",
        "title": "Allow failure",
        "version": 1,
        "capability": "CAP-001",
        "steps": [
            {"id": "s1", "name": "Fail allowed", "command": "exit 1", "allow_failure": True},
            {"id": "s2", "name": "Still runs", "command": "echo done"},
        ],
    }
    path = tmp_path / "WF-006.yaml"
    path.write_text(yaml.dump(defn))
    run = exec_mod.run_workflow(path, runs_dir=runs_dir)
    assert run["status"] == "success"
    assert run["steps"][1]["status"] == "success"


# ---------------------------------------------------------------------------
# Approval gates
# ---------------------------------------------------------------------------

def test_approval_granted_continues(approval_workflow, runs_dir):
    run = exec_mod.run_workflow(
        approval_workflow,
        approval_handler=lambda sid, sname: True,
        runs_dir=runs_dir,
    )
    assert run["status"] == "success"
    approved_step = run["steps"][1]
    assert approved_step["approval_required"] is True
    assert approved_step["approved_by"] == "operator"


def test_approval_denied_aborts(approval_workflow, runs_dir):
    with pytest.raises(exec_mod.WorkflowError, match="aborted"):
        exec_mod.run_workflow(
            approval_workflow,
            approval_handler=lambda sid, sname: False,
            runs_dir=runs_dir,
        )
    saved = run_log_mod.list_runs(runs_dir)
    run = run_log_mod.load_run(saved[0])
    assert run["status"] == "aborted"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_run_raises_for_missing_definition_file(tmp_path, runs_dir):
    with pytest.raises(exec_mod.WorkflowError, match="not found"):
        exec_mod.run_workflow(tmp_path / "nonexistent.yaml", runs_dir=runs_dir)


def test_run_raises_for_invalid_definition(tmp_path, runs_dir):
    path = tmp_path / "invalid.yaml"
    path.write_text("title: Missing id\nsteps: []")
    with pytest.raises(exec_mod.WorkflowError, match="invalid"):
        exec_mod.run_workflow(path, runs_dir=runs_dir)
