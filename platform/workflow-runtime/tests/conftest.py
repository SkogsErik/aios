"""
conftest.py — Shared fixtures for workflow runtime tests.
"""

import sys
from pathlib import Path

import pytest

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _write_workflow(path: Path, definition: dict) -> Path:
    """Write a workflow definition YAML to path."""
    import yaml
    path.write_text(yaml.dump(definition, default_flow_style=False), encoding="utf-8")
    return path


@pytest.fixture()
def runs_dir(tmp_path):
    d = tmp_path / "runs"
    d.mkdir()
    return d


@pytest.fixture()
def simple_workflow(tmp_path):
    """A minimal valid workflow that echoes a message."""
    defn = {
        "id": "WF-001",
        "title": "Simple Echo Workflow",
        "version": 1,
        "capability": "CAP-001",
        "description": "A test workflow.",
        "inputs": [{"name": "message", "description": "Message to echo.", "required": True}],
        "steps": [
            {"id": "step-1", "name": "Echo", "command": "echo {message}",
             "requires_approval": False},
        ],
    }
    path = tmp_path / "WF-001-simple.yaml"
    return _write_workflow(path, defn)


@pytest.fixture()
def two_step_workflow(tmp_path):
    """A workflow with two sequential steps."""
    defn = {
        "id": "WF-002",
        "title": "Two-Step Workflow",
        "version": 1,
        "capability": "CAP-001",
        "steps": [
            {"id": "step-1", "name": "First", "command": "echo step1"},
            {"id": "step-2", "name": "Second", "command": "echo step2"},
        ],
    }
    path = tmp_path / "WF-002-two-step.yaml"
    return _write_workflow(path, defn)


@pytest.fixture()
def approval_workflow(tmp_path):
    """A workflow that requires operator approval before step 2."""
    defn = {
        "id": "WF-003",
        "title": "Approval Workflow",
        "version": 1,
        "capability": "CAP-001",
        "steps": [
            {"id": "step-1", "name": "Before approval", "command": "echo before"},
            {"id": "step-2", "name": "Needs approval", "command": "echo approved",
             "requires_approval": True},
        ],
    }
    path = tmp_path / "WF-003-approval.yaml"
    return _write_workflow(path, defn)


@pytest.fixture()
def failing_workflow(tmp_path):
    """A workflow whose first step fails."""
    defn = {
        "id": "WF-004",
        "title": "Failing Workflow",
        "version": 1,
        "capability": "CAP-001",
        "steps": [
            {"id": "step-1", "name": "Fail", "command": "exit 1", "allow_failure": False},
        ],
    }
    path = tmp_path / "WF-004-fail.yaml"
    return _write_workflow(path, defn)
