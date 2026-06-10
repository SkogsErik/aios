"""
test_run_log.py — Tests for run record creation and persistence.
"""

import yaml
import pytest

import run_log as run_log_mod


def _sample_workflow():
    return {"id": "WF-001", "title": "Test Workflow", "version": 1}


# ---------------------------------------------------------------------------
# new_run
# ---------------------------------------------------------------------------

def test_new_run_has_required_fields():
    run = run_log_mod.new_run(_sample_workflow(), inputs={"key": "val"})
    assert run["workflow_id"] == "WF-001"
    assert run["status"] == "running"
    assert run["steps"] == []
    assert run["inputs"] == {"key": "val"}
    assert run["started_at"] is not None


# ---------------------------------------------------------------------------
# add_step_result
# ---------------------------------------------------------------------------

def test_add_step_result_appends_step():
    run = run_log_mod.new_run(_sample_workflow(), inputs={})
    run_log_mod.add_step_result(
        run, step_id="s1", step_name="Step One",
        started_at="2026-01-01T00:00:00Z", completed_at="2026-01-01T00:00:01Z",
        exit_code=0, stdout="out", stderr="", approval_required=False, approved_by=None,
    )
    assert len(run["steps"]) == 1
    step = run["steps"][0]
    assert step["id"] == "s1"
    assert step["status"] == "success"
    assert step["exit_code"] == 0


def test_add_step_result_failed_step():
    run = run_log_mod.new_run(_sample_workflow(), inputs={})
    run_log_mod.add_step_result(
        run, step_id="s1", step_name="Fail",
        started_at="2026-01-01T00:00:00Z", completed_at="2026-01-01T00:00:01Z",
        exit_code=1, stdout="", stderr="error output", approval_required=False, approved_by=None,
    )
    assert run["steps"][0]["status"] == "failed"
    assert run["steps"][0]["exit_code"] == 1


# ---------------------------------------------------------------------------
# complete_run / save_run / load_run
# ---------------------------------------------------------------------------

def test_complete_run_sets_status_and_timestamp():
    run = run_log_mod.new_run(_sample_workflow(), inputs={})
    run_log_mod.complete_run(run, "success")
    assert run["status"] == "success"
    assert run["completed_at"] is not None


def test_save_and_load_run(tmp_path):
    run = run_log_mod.new_run(_sample_workflow(), inputs={"x": "1"})
    run_log_mod.complete_run(run, "success")
    path = run_log_mod.save_run(run, runs_dir=tmp_path)
    assert path.exists()
    loaded = run_log_mod.load_run(path)
    assert loaded["workflow_id"] == "WF-001"
    assert loaded["status"] == "success"
    assert loaded["inputs"] == {"x": "1"}


# ---------------------------------------------------------------------------
# list_runs
# ---------------------------------------------------------------------------

def test_list_runs_empty_dir(tmp_path):
    assert run_log_mod.list_runs(tmp_path) == []


def test_list_runs_returns_paths(tmp_path):
    for _ in range(3):
        run = run_log_mod.new_run(_sample_workflow(), inputs={})
        run_log_mod.complete_run(run, "success")
        run_log_mod.save_run(run, runs_dir=tmp_path)
    paths = run_log_mod.list_runs(tmp_path)
    assert len(paths) == 3
