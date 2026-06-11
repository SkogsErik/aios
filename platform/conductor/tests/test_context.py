"""
test_context.py — Tests for conductor context assembly.

Run from repo root:
  PYTHONPATH=platform/conductor/src python3 -m pytest platform/conductor/tests/test_context.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "platform" / "conductor" / "src"))

from context import assemble_context, inject_context


# ---------------------------------------------------------------------------
# Minimal mock stores
# ---------------------------------------------------------------------------


class _MockPersonaStore:
    def __init__(self, data=None):
        self._data = data

    def load(self):
        return self._data


class _MockProject:
    def __init__(self, id, title, status):
        self.id = id
        self.title = title
        self.status = status


class _MockProjectStore:
    def __init__(self, projects=None):
        self._projects = projects or []

    def list_active(self):
        return self._projects


class _MockGoal:
    def __init__(self, id, title):
        self.id = id
        self.title = title


class _MockGoalStore:
    def __init__(self, goals=None):
        self._goals = goals or []

    def list_active(self):
        return self._goals


class _MockFocusArea:
    def __init__(self, id, title, attention_budget=None):
        self.id = id
        self.title = title
        self.attention_budget = attention_budget


class _MockFocusStore:
    def __init__(self, areas=None):
        self._areas = areas or []

    def list_active(self):
        return self._areas


# ===========================================================================
# assemble_context
# ===========================================================================


class TestAssembleContext:
    def test_empty_stores_returns_empty_string(self):
        result = assemble_context(
            persona_store=_MockPersonaStore(None),
            project_store=_MockProjectStore([]),
            goal_store=_MockGoalStore([]),
            focus_store=_MockFocusStore([]),
        )
        assert result == ""

    def test_no_stores_returns_empty_string(self):
        assert assemble_context() == ""

    def test_includes_operator_name(self):
        persona = {"operator_name": "Erik", "declared_values": []}
        result = assemble_context(persona_store=_MockPersonaStore(persona))
        assert "Erik" in result

    def test_includes_values(self):
        persona = {
            "operator_name": "Erik",
            "declared_values": [
                {"statement": "Ownership"},
                {"statement": "Clarity"},
            ],
        }
        result = assemble_context(persona_store=_MockPersonaStore(persona))
        assert "Ownership" in result

    def test_includes_projects(self):
        projects = [
            _MockProject("PRJ-001", "AIOS Core", "active"),
            _MockProject("PRJ-002", "Conductor", "active"),
        ]
        result = assemble_context(project_store=_MockProjectStore(projects))
        assert "PRJ-001" in result
        assert "AIOS Core" in result
        assert "PRJ-002" in result

    def test_includes_goals(self):
        goals = [_MockGoal("GL-001", "Ship AIOS v1")]
        result = assemble_context(goal_store=_MockGoalStore(goals))
        assert "GL-001" in result
        assert "Ship AIOS v1" in result

    def test_includes_focus_areas(self):
        areas = [_MockFocusArea("FCA-001", "Engineering", "primary")]
        result = assemble_context(focus_store=_MockFocusStore(areas))
        assert "FCA-001" in result
        assert "Engineering" in result
        assert "primary" in result

    def test_has_header_and_footer(self):
        persona = {"operator_name": "Erik"}
        result = assemble_context(persona_store=_MockPersonaStore(persona))
        assert result.startswith("=== AIOS Context ===")
        assert "===================" in result

    def test_respects_max_projects(self):
        projects = [_MockProject(f"PRJ-{i:03d}", f"Project {i}", "active") for i in range(10)]
        result = assemble_context(project_store=_MockProjectStore(projects), max_projects=3)
        assert result.count("PRJ-") == 3

    def test_store_exception_is_swallowed(self):
        class BrokenStore:
            def load(self):
                raise RuntimeError("broken")
            def list_active(self):
                raise RuntimeError("broken")

        # Should not raise, returns empty or partial result
        result = assemble_context(
            persona_store=BrokenStore(),
            project_store=BrokenStore(),
        )
        assert isinstance(result, str)


# ===========================================================================
# inject_context
# ===========================================================================


class TestInjectContext:
    def test_injects_context_before_prompt(self):
        context = "=== AIOS Context ===\nOperator: Erik\n==================="
        prompt = "What is Python?"
        result = inject_context(prompt, context)
        assert result.startswith(context)
        assert prompt in result

    def test_empty_context_returns_prompt_unchanged(self):
        prompt = "Hello"
        assert inject_context(prompt, "") == prompt

    def test_separator_between_context_and_prompt(self):
        context = "ctx"
        prompt = "msg"
        result = inject_context(prompt, context)
        assert "\n\n" in result
