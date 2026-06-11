"""
test_project_store.py — Tests for ProjectStore, CommitmentStore, and PersonaStore.

Run from repo root:
  PYTHONPATH=wyrd/src:platform/executive-daemon/src python3 -m pytest wyrd/tests/test_project_store.py -q
"""

import datetime
import tempfile
from pathlib import Path

import pytest

import sys
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "wyrd" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "platform" / "executive-daemon" / "src"))

from project_store import (
    CommitmentData,
    CommitmentStore,
    DeclaredFact,
    Persona,
    PersonaStore,
    PersonaValue,
    Project,
    ProjectStore,
    _parse_date,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today() -> datetime.date:
    return datetime.date.today()


def make_project(store: ProjectStore, title: str = "Test Project", **kwargs) -> Project:
    project_id = store.next_id()
    today = _today()
    p = Project(
        id=project_id,
        title=title,
        type=kwargs.get("type", "project"),
        status=kwargs.get("status", "active"),
        created=today,
        updated=today,
        priority_weight=kwargs.get("priority_weight", 0.5),
        attention_state=kwargs.get("attention_state", "active"),
        last_touch=today,
        **{k: v for k, v in kwargs.items() if k not in ("type", "status", "priority_weight", "attention_state")},
    )
    store.save(p)
    return p


def make_commitment(store: CommitmentStore, description: str = "Do something", days: int = 7, **kwargs) -> CommitmentData:
    cmt_id = store.next_id()
    today = _today()
    c = CommitmentData(
        id=cmt_id,
        description=description,
        deadline=today + datetime.timedelta(days=days),
        status=kwargs.get("status", "active"),
        created=today,
        updated=today,
        weight=kwargs.get("weight", 0.5),
        project=kwargs.get("project"),
    )
    store.save(c)
    return c


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_iso_string(self):
        assert _parse_date("2025-06-01") == datetime.date(2025, 6, 1)

    def test_date_object_passthrough(self):
        d = datetime.date(2025, 1, 1)
        assert _parse_date(d) == d

    def test_none_returns_none(self):
        assert _parse_date(None) is None

    def test_invalid_returns_none(self):
        assert _parse_date("not-a-date") is None

    def test_datetime_truncated_to_date(self):
        result = _parse_date("2025-06-01T12:00:00")
        assert result == datetime.date(2025, 6, 1)


# ---------------------------------------------------------------------------
# ProjectStore
# ---------------------------------------------------------------------------

class TestProjectStoreNextId:
    def test_first_id_is_001(self, tmp_path):
        store = ProjectStore(tmp_path)
        assert store.next_id() == "PRJ-001"

    def test_sequential_after_save(self, tmp_path):
        store = ProjectStore(tmp_path)
        make_project(store)
        assert store.next_id() == "PRJ-002"

    def test_gap_fills_to_max_plus_one(self, tmp_path):
        """Even with a gap (PRJ-001, PRJ-003), next ID is PRJ-004."""
        store = ProjectStore(tmp_path)
        p1 = make_project(store, "A")
        p2 = make_project(store, "B")
        p3 = make_project(store, "C")
        # Delete PRJ-002 to create a gap
        (tmp_path / f"{p2.id}.yaml").unlink()
        assert store.next_id() == "PRJ-004"


class TestProjectStoreSaveGet:
    def test_save_and_retrieve(self, tmp_path):
        store = ProjectStore(tmp_path)
        p = make_project(store, "My Project")
        loaded = store.get(p.id)
        assert loaded is not None
        assert loaded.id == p.id
        assert loaded.title == "My Project"
        assert loaded.status == "active"

    def test_get_nonexistent_returns_none(self, tmp_path):
        store = ProjectStore(tmp_path)
        assert store.get("PRJ-999") is None

    def test_all_fields_round_trip(self, tmp_path):
        store = ProjectStore(tmp_path)
        today = _today()
        p = Project(
            id="PRJ-001",
            title="Full project",
            type="initiative",
            status="paused",
            created=today,
            updated=today,
            goal="GL-001",
            focus_area="FCA-002",
            description="A description",
            outcome_statement="Done when X",
            target_completion=today + datetime.timedelta(days=30),
            attention_state="dormant",
            last_touch=today - datetime.timedelta(days=10),
            health="at_risk",
            priority_weight=0.9,
            tags=["alpha", "beta"],
            commitments=["CMT-001", "CMT-002"],
        )
        store.save(p)
        loaded = store.get("PRJ-001")
        assert loaded.goal == "GL-001"
        assert loaded.focus_area == "FCA-002"
        assert loaded.type == "initiative"
        assert loaded.health == "at_risk"
        assert loaded.priority_weight == pytest.approx(0.9)
        assert loaded.tags == ["alpha", "beta"]
        assert loaded.commitments == ["CMT-001", "CMT-002"]
        assert loaded.target_completion == today + datetime.timedelta(days=30)

    def test_save_is_atomic(self, tmp_path):
        """No .tmp file should remain after save."""
        store = ProjectStore(tmp_path)
        p = make_project(store, "Atomic")
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []


class TestProjectStoreList:
    def test_list_all(self, tmp_path):
        store = ProjectStore(tmp_path)
        make_project(store, "A", status="active")
        make_project(store, "B", status="completed")
        make_project(store, "C", status="paused")
        assert len(store.list_all()) == 3

    def test_list_active_excludes_terminal(self, tmp_path):
        store = ProjectStore(tmp_path)
        make_project(store, "Active", status="active")
        make_project(store, "Completed", status="completed")
        make_project(store, "Cancelled", status="cancelled")
        make_project(store, "Abandoned", status="abandoned")
        active = store.list_active()
        assert len(active) == 1
        assert active[0].title == "Active"

    def test_list_active_includes_at_risk_and_stalled(self, tmp_path):
        store = ProjectStore(tmp_path)
        make_project(store, "AtRisk", status="at_risk")
        make_project(store, "Stalled", status="stalled")
        assert len(store.list_active()) == 2

    def test_list_all_empty_dir(self, tmp_path):
        store = ProjectStore(tmp_path / "nonexistent")
        assert store.list_all() == []


class TestProjectStoreTouchAndUpdate:
    def test_touch_updates_last_touch(self, tmp_path):
        store = ProjectStore(tmp_path)
        p = make_project(store, "Touch me", attention_state="active")
        yesterday = _today() - datetime.timedelta(days=1)
        updated = store.touch(p.id, when=yesterday)
        assert updated.last_touch == yesterday

    def test_touch_resurfaces_dormant(self, tmp_path):
        store = ProjectStore(tmp_path)
        today = _today()
        p = Project(
            id="PRJ-001",
            title="Dormant",
            type="project",
            status="active",
            created=today,
            updated=today,
            attention_state="dormant",
            last_touch=today - datetime.timedelta(days=14),
        )
        store.save(p)
        updated = store.touch("PRJ-001")
        assert updated.attention_state == "resurfaced"

    def test_touch_nonexistent_returns_none(self, tmp_path):
        store = ProjectStore(tmp_path)
        assert store.touch("PRJ-999") is None

    def test_update_status(self, tmp_path):
        store = ProjectStore(tmp_path)
        p = make_project(store, "Status test")
        updated = store.update_status(p.id, "completed")
        assert updated.status == "completed"
        loaded = store.get(p.id)
        assert loaded.status == "completed"

    def test_update_attention_state(self, tmp_path):
        store = ProjectStore(tmp_path)
        p = make_project(store, "Attention test")
        updated = store.update_attention_state(p.id, "forgotten")
        assert updated.attention_state == "forgotten"


class TestProjectStoreAsTrackedItems:
    def test_terminal_projects_excluded(self, tmp_path):
        store = ProjectStore(tmp_path)
        make_project(store, "Active", status="active")
        make_project(store, "Done", status="completed")
        make_project(store, "Cancelled", status="cancelled")
        items = store.list_as_tracked_items()
        assert len(items) == 1
        assert items[0].id.startswith("PRJ-")

    def test_tracked_item_fields(self, tmp_path):
        store = ProjectStore(tmp_path)
        p = make_project(store, "Item", attention_state="dormant")
        items = store.list_as_tracked_items()
        assert len(items) == 1
        item = items[0]
        assert item.id == p.id
        assert item.kind == "project"

    def test_unknown_attention_state_defaults_to_active(self, tmp_path):
        store = ProjectStore(tmp_path)
        today = _today()
        p = Project(
            id="PRJ-001",
            title="BadState",
            type="project",
            status="active",
            created=today,
            updated=today,
            attention_state="INVALID_STATE",
            last_touch=today,
        )
        store.save(p)
        items = store.list_as_tracked_items()
        from attention_manager import AttentionState
        assert items[0].attention_state == AttentionState.ACTIVE


# ---------------------------------------------------------------------------
# CommitmentStore
# ---------------------------------------------------------------------------

class TestCommitmentStoreNextId:
    def test_first_id_is_001(self, tmp_path):
        store = CommitmentStore(tmp_path)
        assert store.next_id() == "CMT-001"

    def test_sequential(self, tmp_path):
        store = CommitmentStore(tmp_path)
        make_commitment(store)
        assert store.next_id() == "CMT-002"


class TestCommitmentStoreSaveGet:
    def test_save_and_retrieve(self, tmp_path):
        store = CommitmentStore(tmp_path)
        c = make_commitment(store, "Deliver report", days=5)
        loaded = store.get(c.id)
        assert loaded is not None
        assert loaded.description == "Deliver report"
        assert loaded.status == "active"

    def test_get_nonexistent_returns_none(self, tmp_path):
        store = CommitmentStore(tmp_path)
        assert store.get("CMT-999") is None

    def test_atomic_write_no_tmp_files(self, tmp_path):
        store = CommitmentStore(tmp_path)
        make_commitment(store)
        assert list(tmp_path.glob("*.tmp")) == []

    def test_all_fields_round_trip(self, tmp_path):
        store = CommitmentStore(tmp_path)
        today = _today()
        c = CommitmentData(
            id="CMT-001",
            description="Full commitment",
            deadline=today + datetime.timedelta(days=14),
            status="active",
            created=today,
            updated=today,
            project="PRJ-001",
            promisee="team",
            weight=0.8,
            consequences="Project delayed",
            notes="Agreed in standup",
        )
        store.save(c)
        loaded = store.get("CMT-001")
        assert loaded.project == "PRJ-001"
        assert loaded.promisee == "team"
        assert loaded.weight == pytest.approx(0.8)
        assert loaded.consequences == "Project delayed"
        assert loaded.notes == "Agreed in standup"


class TestCommitmentStoreList:
    def test_list_active(self, tmp_path):
        store = CommitmentStore(tmp_path)
        make_commitment(store, status="active")
        make_commitment(store, status="fulfilled")
        make_commitment(store, status="broken")
        assert len(store.list_active()) == 1

    def test_list_all(self, tmp_path):
        store = CommitmentStore(tmp_path)
        for _ in range(3):
            make_commitment(store)
        assert len(store.list_all()) == 3

    def test_list_empty(self, tmp_path):
        store = CommitmentStore(tmp_path / "empty")
        assert store.list_all() == []


class TestCommitmentStoreAsRulesEngine:
    def test_only_active_exported(self, tmp_path):
        store = CommitmentStore(tmp_path)
        make_commitment(store, "Active one", status="active")
        make_commitment(store, "Fulfilled", status="fulfilled")
        rules_cmts = store.list_as_rules_engine_commitments()
        assert len(rules_cmts) == 1

    def test_rules_engine_types(self, tmp_path):
        store = CommitmentStore(tmp_path)
        today = _today()
        c = CommitmentData(
            id="CMT-001",
            description="Test",
            deadline=today + datetime.timedelta(days=3),
            status="active",
            created=today,
            updated=today,
            weight=0.7,
        )
        store.save(c)
        from rules_engine import Commitment
        result = store.list_as_rules_engine_commitments()
        assert len(result) == 1
        assert isinstance(result[0], Commitment)
        assert result[0].id == "CMT-001"
        assert result[0].weight == pytest.approx(0.7)
        assert result[0].deadline == today + datetime.timedelta(days=3)


# ---------------------------------------------------------------------------
# PersonaStore
# ---------------------------------------------------------------------------

class TestPersonaStoreInit:
    def test_init_creates_file(self, tmp_path):
        store = PersonaStore(tmp_path)
        assert not store.exists()
        persona = store.init(name="Test User")
        assert store.exists()
        assert persona.id == "PRS-001"
        assert persona.name == "Test User"

    def test_init_twice_raises(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init()
        with pytest.raises(FileExistsError):
            store.init()

    def test_load_nonexistent_returns_none(self, tmp_path):
        store = PersonaStore(tmp_path / "empty")
        assert store.load() is None


class TestPersonaStoreRoundTrip:
    def test_save_and_load(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init(name="Dev")
        persona = store.load()
        assert persona.id == "PRS-001"
        assert persona.name == "Dev"
        assert persona.version >= 1

    def test_version_increments_on_save(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init()
        p = store.load()   # read what was actually persisted
        v1 = p.version
        store.save(p)
        v2 = store.load().version
        assert v2 > v1

    def test_add_value(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init()
        store.add_value("Deep work", priority=1, category="professional")
        persona = store.load()
        assert len(persona.values) == 1
        val = persona.values[0]
        val_text = val.get("value") if isinstance(val, dict) else val.value
        assert val_text == "Deep work"

    def test_add_multiple_values(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init()
        store.add_value("Deep work", priority=1, category="professional")
        store.add_value("Family", priority=2, category="personal")
        persona = store.load()
        assert len(persona.values) == 2

    def test_add_fact(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init()
        store.add_fact("I prefer async communication", category="preference", confidence="high")
        persona = store.load()
        assert len(persona.declared_facts) == 1
        fact = persona.declared_facts[0]
        stmt = fact.get("statement") if isinstance(fact, dict) else fact.statement
        assert "async" in stmt

    def test_atomic_write_no_tmp_files(self, tmp_path):
        store = PersonaStore(tmp_path)
        store.init()
        assert list(tmp_path.glob("*.tmp")) == []
