"""
test_goal_store.py — Tests for GoalStore and FocusAreaStore.

Run from repo root:
  PYTHONPATH=wyrd/src python3 -m pytest wyrd/tests/test_goal_store.py -q
"""

import datetime
from pathlib import Path

import pytest
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "wyrd" / "src"))

from goal_store import Goal, GoalStore, FocusArea, FocusAreaStore


# ===========================================================================
# GoalStore
# ===========================================================================


class TestGoalStoreNextId:
    def test_first_id_is_001(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        assert store.next_id() == "GL-001"

    def test_increments_past_existing(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g = store.init("First goal")
        assert g.id == "GL-001"
        assert store.next_id() == "GL-002"

    def test_no_gap_in_sequence(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        store.init("Goal A")
        store.init("Goal B")
        assert store.next_id() == "GL-003"


class TestGoalStoreInit:
    def test_creates_goal_with_defaults(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g = store.init("Learn Rust")
        assert g.id == "GL-001"
        assert g.title == "Learn Rust"
        assert g.type == "outcome"
        assert g.status == "draft"
        assert g.created == datetime.date.today()
        assert g.priority_weight == 0.5

    def test_creates_goal_with_all_fields(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g = store.init(
            title="Ship AIOS v1",
            type="aspiration",
            horizon="6-month",
            focus_area="FCA-001",
            description="Release AIOS",
            why="Personal autonomy",
            outcome_statement="v1 tagged and published",
            target_date=datetime.date(2025, 12, 31),
            priority_weight=0.9,
            tags=["engineering", "product"],
        )
        assert g.type == "aspiration"
        assert g.horizon == "6-month"
        assert g.focus_area == "FCA-001"
        assert g.why == "Personal autonomy"
        assert g.target_date == datetime.date(2025, 12, 31)
        assert g.priority_weight == 0.9
        assert "engineering" in g.tags

    def test_persists_to_disk(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        store.init("Persisted goal")
        assert (tmp_path / "GL-001.yaml").exists()


class TestGoalStoreGet:
    def test_get_returns_goal(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        store.init("Readable goal")
        g = store.get("GL-001")
        assert g is not None
        assert g.title == "Readable goal"

    def test_get_missing_returns_none(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        assert store.get("GL-999") is None

    def test_get_roundtrips_dates(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        target = datetime.date(2025, 6, 15)
        store.init("Dated goal", target_date=target)
        g = store.get("GL-001")
        assert g.target_date == target
        assert isinstance(g.created, datetime.date)


class TestGoalStoreList:
    def test_list_all_empty(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        assert store.list_all() == []

    def test_list_all_returns_all(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        store.init("A")
        store.init("B")
        store.init("C")
        assert len(store.list_all()) == 3

    def test_list_active_filters_by_status(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g1 = store.init("Draft goal")
        g2 = store.init("Active goal")
        store.update_status(g2.id, "active")
        active = store.list_active()
        assert len(active) == 1
        assert active[0].id == g2.id


class TestGoalStoreUpdateStatus:
    def test_update_status(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g = store.init("Status test")
        updated = store.update_status(g.id, "active")
        assert updated.status == "active"
        assert store.get(g.id).status == "active"

    def test_update_status_missing_returns_none(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        assert store.update_status("GL-999", "active") is None


class TestGoalStoreLinkProject:
    def test_link_project(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g = store.init("Linked goal")
        updated = store.link_project(g.id, "PRJ-001")
        assert "PRJ-001" in updated.projects

    def test_link_project_idempotent(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        g = store.init("Idempotent link")
        store.link_project(g.id, "PRJ-001")
        store.link_project(g.id, "PRJ-001")
        g_fresh = store.get(g.id)
        assert g_fresh.projects.count("PRJ-001") == 1

    def test_link_missing_goal_returns_none(self, tmp_path):
        store = GoalStore(base_dir=tmp_path)
        assert store.link_project("GL-999", "PRJ-001") is None


# ===========================================================================
# FocusAreaStore
# ===========================================================================


class TestFocusAreaStoreNextId:
    def test_first_id_is_001(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        assert store.next_id() == "FCA-001"

    def test_increments_past_existing(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        store.init("Engineering")
        assert store.next_id() == "FCA-002"


class TestFocusAreaStoreInit:
    def test_creates_area_with_defaults(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        a = store.init("Engineering")
        assert a.id == "FCA-001"
        assert a.title == "Engineering"
        assert a.status == "active"
        assert a.goals == []

    def test_creates_area_with_all_fields(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        a = store.init(
            title="Health",
            description="Physical and mental wellbeing",
            why_it_matters="Foundation for everything else",
            attention_budget="primary",
            tags=["wellbeing"],
        )
        assert a.attention_budget == "primary"
        assert "wellbeing" in a.tags

    def test_persists_to_disk(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        store.init("Saved area")
        assert (tmp_path / "FCA-001.yaml").exists()


class TestFocusAreaStoreGet:
    def test_get_returns_area(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        store.init("Gettable")
        a = store.get("FCA-001")
        assert a is not None
        assert a.title == "Gettable"

    def test_get_missing_returns_none(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        assert store.get("FCA-999") is None

    def test_get_roundtrips_dates(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        store.init("Dated area")
        a = store.get("FCA-001")
        assert isinstance(a.created, datetime.date)


class TestFocusAreaStoreList:
    def test_list_all_empty(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        assert store.list_all() == []

    def test_list_all_returns_all(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        store.init("A")
        store.init("B")
        assert len(store.list_all()) == 2

    def test_list_active_filters_archived(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        a1 = store.init("Active area")
        a2 = store.init("Archived area")
        store.update_status(a2.id, "archived")
        active = store.list_active()
        assert len(active) == 1
        assert active[0].id == a1.id


class TestFocusAreaStoreUpdateStatus:
    def test_update_status(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        a = store.init("Status area")
        updated = store.update_status(a.id, "paused")
        assert updated.status == "paused"
        assert store.get(a.id).status == "paused"

    def test_update_status_missing_returns_none(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        assert store.update_status("FCA-999", "archived") is None


class TestFocusAreaStoreLinkGoal:
    def test_link_goal(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        a = store.init("Area with goal")
        updated = store.link_goal(a.id, "GL-001")
        assert "GL-001" in updated.goals

    def test_link_goal_idempotent(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        a = store.init("Idempotent")
        store.link_goal(a.id, "GL-001")
        store.link_goal(a.id, "GL-001")
        a_fresh = store.get(a.id)
        assert a_fresh.goals.count("GL-001") == 1

    def test_link_missing_area_returns_none(self, tmp_path):
        store = FocusAreaStore(base_dir=tmp_path)
        assert store.link_goal("FCA-999", "GL-001") is None
