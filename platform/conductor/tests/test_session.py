"""
test_session.py — Tests for conductor SessionStore.

Run from repo root:
  PYTHONPATH=platform/conductor/src python3 -m pytest platform/conductor/tests/test_session.py -q
"""

import datetime
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "platform" / "conductor" / "src"))

from session import SessionStore, make_turn, make_session


class TestSessionStoreNextId:
    def test_first_id_format(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        today = datetime.date(2026, 6, 11)
        sid = store.next_id(when=today)
        assert sid == "SES-2026-0611-001"

    def test_increments_same_day(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        today = datetime.date(2026, 6, 11)
        store.create(when=today)
        assert store.next_id(when=today) == "SES-2026-0611-002"

    def test_independent_across_days(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        store.create(when=datetime.date(2026, 6, 10))
        assert store.next_id(when=datetime.date(2026, 6, 11)) == "SES-2026-0611-001"


class TestSessionStoreCreate:
    def test_creates_session(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create(title="Test session")
        assert s["title"] == "Test session"
        assert s["status"] == "active"
        assert s["turns"] == []

    def test_persists_to_disk(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        assert (tmp_path / f"{s['id']}.yaml").exists()

    def test_creates_with_context_snapshot(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create(context_snapshot={"key": "value"})
        assert s["context_snapshot"]["key"] == "value"

    def test_no_title(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        assert s["title"] is None


class TestSessionStoreGet:
    def test_get_returns_session(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create(title="Readable")
        fetched = store.get(s["id"])
        assert fetched is not None
        assert fetched["title"] == "Readable"

    def test_get_missing_returns_none(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        assert store.get("SES-2099-0101-001") is None

    def test_get_has_turns_list(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        fetched = store.get(s["id"])
        assert isinstance(fetched["turns"], list)


class TestSessionStoreAddTurn:
    def test_adds_turn(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        turn = make_turn("user", "Hello!")
        updated = store.add_turn(s["id"], turn)
        assert len(updated["turns"]) == 1
        assert updated["turns"][0]["role"] == "user"
        assert updated["turns"][0]["content"] == "Hello!"

    def test_adds_multiple_turns(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        store.add_turn(s["id"], make_turn("user", "Q1"))
        store.add_turn(s["id"], make_turn("assistant", "A1"))
        store.add_turn(s["id"], make_turn("user", "Q2"))
        updated = store.get(s["id"])
        assert len(updated["turns"]) == 3
        assert updated["turns"][2]["content"] == "Q2"

    def test_add_turn_missing_session_returns_none(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        assert store.add_turn("SES-2099-0101-001", make_turn("user", "hi")) is None

    def test_turn_has_timestamp(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        turn = make_turn("user", "timestamped")
        store.add_turn(s["id"], turn)
        updated = store.get(s["id"])
        assert "timestamp" in updated["turns"][0]

    def test_turn_tool_field(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        turn = make_turn("assistant", "response", tool="research")
        store.add_turn(s["id"], turn)
        updated = store.get(s["id"])
        assert updated["turns"][0]["tool"] == "research"


class TestSessionStoreList:
    def test_list_all_empty(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        assert store.list_all() == []

    def test_list_all_returns_all(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        store.create()
        store.create()
        assert len(store.list_all()) == 2

    def test_list_active_filters_archived(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s1 = store.create(title="Active")
        s2 = store.create(title="Archived")
        store.archive(s2["id"])
        active = store.list_active()
        assert len(active) == 1
        assert active[0]["id"] == s1["id"]


class TestSessionStoreArchive:
    def test_archive_sets_status(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        s = store.create()
        archived = store.archive(s["id"])
        assert archived["status"] == "archived"
        assert store.get(s["id"])["status"] == "archived"

    def test_archive_missing_returns_none(self, tmp_path):
        store = SessionStore(base_dir=tmp_path)
        assert store.archive("SES-2099-0101-001") is None


class TestMakeTurn:
    def test_make_turn_fields(self):
        t = make_turn("user", "hello")
        assert t["role"] == "user"
        assert t["content"] == "hello"
        assert "timestamp" in t
        assert t["tool"] is None

    def test_make_turn_with_tool(self):
        t = make_turn("assistant", "result", tool="plan")
        assert t["tool"] == "plan"
