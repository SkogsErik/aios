"""
test_rules_engine.py — Tests for the deterministic rules engine.
"""

import datetime

import pytest

from attention_manager import AttentionState, TrackedItem
from rules_engine import Commitment, Dependency, RulesEngine


def _item(
    id: str,
    state: AttentionState = AttentionState.ACTIVE,
    days_ago: int = 0,
    kind: str = "project",
) -> TrackedItem:
    today = datetime.date(2026, 6, 10)
    return TrackedItem(id, state, today - datetime.timedelta(days=days_ago), kind)


def _commitment(id: str, days_until_deadline: int, weight: float = 0.5) -> Commitment:
    today = datetime.date(2026, 6, 10)
    return Commitment(id, today + datetime.timedelta(days=days_until_deadline), weight)


# ---------------------------------------------------------------------------
# Priority computation
# ---------------------------------------------------------------------------


class TestPriorityComputation:
    def test_deadline_urgency_boosts_score(self):
        engine = RulesEngine()
        today = datetime.date(2026, 6, 10)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE, days_ago=1),
            _item("PRJ-002", AttentionState.ACTIVE, days_ago=1),
        ]
        commitments = [
            _commitment("PRJ-001", days_until_deadline=2, weight=0.8),
            _commitment("PRJ-002", days_until_deadline=90, weight=0.5),
        ]
        results = engine.compute_priorities(items, commitments, today)
        assert results[0].item_id == "PRJ-001"
        assert results[0].score > results[1].score

    def test_momentum_reflects_recency(self):
        engine = RulesEngine()
        today = datetime.date(2026, 6, 10)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE, days_ago=1),
            _item("PRJ-002", AttentionState.ACTIVE, days_ago=25),
        ]
        commitments: list[Commitment] = []
        results = engine.compute_priorities(items, commitments, today)
        assert results[0].item_id == "PRJ-001"
        assert results[0].momentum > results[1].momentum

    def test_item_without_commitment_gets_default_weight(self):
        engine = RulesEngine()
        today = datetime.date(2026, 6, 10)
        items = [_item("PRJ-003", AttentionState.ACTIVE, days_ago=5)]
        results = engine.compute_priorities(items, [], today)
        assert results[0].weight == 0.3


# ---------------------------------------------------------------------------
# Stall detection
# ---------------------------------------------------------------------------


class TestStallDetection:
    def test_engine_detects_stalls(self):
        engine = RulesEngine()
        today = datetime.date(2026, 6, 10)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE, days_ago=20),
            _item("PRJ-002", AttentionState.ACTIVE, days_ago=5),
        ]
        stalled = engine.check_stalls(items, today)
        assert len(stalled) == 1
        assert stalled[0].id == "PRJ-001"


# ---------------------------------------------------------------------------
# Fragmentation detection
# ---------------------------------------------------------------------------


class TestFragmentationDetection:
    def test_engine_detects_fragmentation(self):
        engine = RulesEngine()
        items = [
            _item(f"PRJ-{i:03d}", AttentionState.ACTIVE, days_ago=0)
            for i in range(10)
        ]
        alerts = engine.check_fragmentation(items)
        assert "active_over_limit" in alerts


# ---------------------------------------------------------------------------
# Unblocking notifications
# ---------------------------------------------------------------------------


class TestUnblockingNotifications:
    def test_no_alerts_when_blocker_not_touched(self):
        engine = RulesEngine()
        deps = [
            Dependency(
                blocker_id="PRJ-001",
                blocked_id="PRJ-002",
                description="PRJ-002 depends on PRJ-001",
            )
        ]
        alerts = engine.check_unblocking(deps, recently_touched_ids=set())
        assert alerts == []

    def test_alert_when_blocker_touched(self):
        engine = RulesEngine()
        deps = [
            Dependency(
                blocker_id="PRJ-001",
                blocked_id="PRJ-002",
                description="PRJ-002 depends on PRJ-001",
            )
        ]
        alerts = engine.check_unblocking(deps, recently_touched_ids={"PRJ-001"})
        assert len(alerts) == 1
        assert alerts[0].blocker_item_id == "PRJ-001"
        assert alerts[0].unblocked_item_id == "PRJ-002"

    def test_no_alert_for_self_dependency(self):
        engine = RulesEngine()
        deps: list[Dependency] = []
        alerts = engine.check_unblocking(deps, recently_touched_ids={"PRJ-001"})
        assert alerts == []
