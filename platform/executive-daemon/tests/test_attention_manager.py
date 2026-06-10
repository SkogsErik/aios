"""
test_attention_manager.py — Tests for attention state tracking, decay,
stall detection, deadline scoring, and fragmentation detection.
"""

import datetime

import pytest

from attention_manager import (
    AttentionManager,
    AttentionState,
    DeadlineScorer,
    FragmentationDetector,
    StallDetector,
    TrackedItem,
)


def _item(
    id: str,
    state: AttentionState = AttentionState.ACTIVE,
    days_ago: int = 0,
    kind: str = "project",
) -> TrackedItem:
    today = datetime.date(2026, 6, 10)
    return TrackedItem(id, state, today - datetime.timedelta(days=days_ago), kind)


# ---------------------------------------------------------------------------
# Attention decay
# ---------------------------------------------------------------------------


class TestAttentionDecay:
    def test_active_stays_active_when_recent(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.ACTIVE, days_ago=3)
        today = datetime.date(2026, 6, 10)
        assert mgr.compute_next_state(item, today) == AttentionState.ACTIVE

    def test_active_decays_to_dormant_after_threshold(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.ACTIVE, days_ago=10)
        today = datetime.date(2026, 6, 10)
        assert mgr.compute_next_state(item, today) == AttentionState.DORMANT

    def test_dormant_stays_dormant_before_forgotten_threshold(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.DORMANT, days_ago=14)
        today = datetime.date(2026, 6, 10)
        assert mgr.compute_next_state(item, today) == AttentionState.DORMANT

    def test_dormant_decays_to_forgotten_after_threshold(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.DORMANT, days_ago=28)
        today = datetime.date(2026, 6, 10)
        assert mgr.compute_next_state(item, today) == AttentionState.FORGOTTEN

    def test_resurfaced_transitions_to_active(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.RESURFACED, days_ago=0)
        today = datetime.date(2026, 6, 10)
        assert mgr.compute_next_state(item, today) == AttentionState.ACTIVE

    def test_forgotten_stays_forgotten(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.FORGOTTEN, days_ago=60)
        today = datetime.date(2026, 6, 10)
        assert mgr.compute_next_state(item, today) == AttentionState.FORGOTTEN


class TestTouchItem:
    def test_touch_active_keeps_active_and_resets_timer(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.ACTIVE, days_ago=50)
        today = datetime.date(2026, 6, 10)
        touched = mgr.touch_item(item, today)
        assert touched.last_touch == today
        assert touched.attention_state == AttentionState.ACTIVE

    def test_touch_dormant_resurfaces(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.DORMANT, days_ago=50)
        today = datetime.date(2026, 6, 10)
        touched = mgr.touch_item(item, today)
        assert touched.attention_state == AttentionState.RESURFACED
        assert touched.last_touch == today

    def test_touch_forgotten_resurfaces(self):
        mgr = AttentionManager()
        item = _item("PRJ-001", AttentionState.FORGOTTEN, days_ago=50)
        today = datetime.date(2026, 6, 10)
        touched = mgr.touch_item(item, today)
        assert touched.attention_state == AttentionState.RESURFACED


class TestEvaluateAll:
    def test_evaluate_all_reports_only_changes(self):
        mgr = AttentionManager()
        items = [
            _item("PRJ-001", AttentionState.ACTIVE, days_ago=1),
            _item("PRJ-002", AttentionState.ACTIVE, days_ago=10),
            _item("PRJ-003", AttentionState.DORMANT, days_ago=28),
            _item("PRJ-004", AttentionState.FORGOTTEN, days_ago=60),
        ]
        today = datetime.date(2026, 6, 10)
        results = mgr.evaluate_all(items, today)
        assert len(results) == 2
        assert results[0][0].id == "PRJ-002"
        assert results[0][1] == AttentionState.DORMANT
        assert results[1][0].id == "PRJ-003"
        assert results[1][1] == AttentionState.FORGOTTEN


# ---------------------------------------------------------------------------
# Stall detection
# ---------------------------------------------------------------------------


class TestStallDetector:
    def test_no_stalls_when_all_recent(self):
        detector = StallDetector(stall_threshold_days=14)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE, days_ago=5),
            _item("PRJ-002", AttentionState.ACTIVE, days_ago=10),
        ]
        today = datetime.date(2026, 6, 10)
        assert detector.find_stalled(items, today) == []

    def test_stalls_detected_when_beyond_threshold(self):
        detector = StallDetector(stall_threshold_days=14)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE, days_ago=20),
            _item("PRJ-002", AttentionState.ACTIVE, days_ago=10),
        ]
        today = datetime.date(2026, 6, 10)
        stalled = detector.find_stalled(items, today)
        assert len(stalled) == 1
        assert stalled[0].id == "PRJ-001"

    def test_forgotten_items_not_flagged_as_stalled(self):
        detector = StallDetector(stall_threshold_days=14)
        items = [
            _item("PRJ-001", AttentionState.FORGOTTEN, days_ago=100),
        ]
        today = datetime.date(2026, 6, 10)
        assert detector.find_stalled(items, today) == []


# ---------------------------------------------------------------------------
# Deadline scoring
# ---------------------------------------------------------------------------


class TestDeadlineScorer:
    def test_past_deadline_scores_1(self):
        scorer = DeadlineScorer()
        assert scorer.score(-5) == 1.0

    def test_due_today_scores_1(self):
        scorer = DeadlineScorer()
        assert scorer.score(0) == 1.0

    def test_far_future_deadline_scores_low(self):
        scorer = DeadlineScorer()
        score = scorer.score(80)
        assert 0.0 < score < 0.2

    def test_beyond_90_days_scores_0(self):
        scorer = DeadlineScorer()
        assert scorer.score(95) == 0.0


# ---------------------------------------------------------------------------
# Fragmentation detection
# ---------------------------------------------------------------------------


class TestFragmentationDetector:
    def test_no_alerts_below_threshold(self):
        detector = FragmentationDetector(active_limit=3, dormant_limit=5)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE),
            _item("PRJ-002", AttentionState.ACTIVE),
            _item("PRJ-003", AttentionState.DORMANT),
        ]
        assert detector.check(items) == {}

    def test_alert_when_over_active_limit(self):
        detector = FragmentationDetector(active_limit=2, dormant_limit=5)
        items = [
            _item("PRJ-001", AttentionState.ACTIVE),
            _item("PRJ-002", AttentionState.ACTIVE),
            _item("PRJ-003", AttentionState.ACTIVE),
        ]
        alerts = detector.check(items)
        assert "active_over_limit" in alerts
        assert alerts["active_over_limit"] == 3

    def test_alert_when_over_dormant_limit(self):
        detector = FragmentationDetector(active_limit=5, dormant_limit=2)
        items = [
            _item("PRJ-001", AttentionState.DORMANT),
            _item("PRJ-002", AttentionState.DORMANT),
            _item("PRJ-003", AttentionState.DORMANT),
        ]
        alerts = detector.check(items)
        assert "dormant_over_limit" in alerts
        assert alerts["dormant_over_limit"] == 3
