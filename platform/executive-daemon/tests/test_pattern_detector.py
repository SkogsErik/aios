"""
test_pattern_detector.py — Tests for all 7 pattern detection rules.
"""

import datetime

import pytest

from learning_engine import (
    AggregatedWindow,
    FeedbackAction,
    Observation,
    PatternType,
)
from pattern_detector import (
    AttentionCliffDetector,
    BehavioralBiasDetector,
    CategoryAssignment,
    CompletionSignatureDetector,
    CyclicalPatternDetector,
    DelegationPatternDetector,
    EnergyCorrelationDetector,
    ProjectPriorityPair,
    RejectionPatternDetector,
)


def _obs(
    summary: str = "x",
    type: str = "action",
    project: str | None = "PRJ-001",
    energy: str | None = "high",
    tags: list[str] | None = None,
    source_component: str = "cli",
    weekday: int = 0,  # monday
) -> Observation:
    return Observation(
        id="OBS-T",
        timestamp=datetime.datetime(2026, 6, 8 + weekday, 14, 0),
        type=type,
        source_mechanism="auto",
        source_component=source_component,
        summary=summary,
        project=project,
        energy=energy,
        tags=tags or [],
    )


def _win(
    projects: dict[str, int] | None = None,
    types: dict[str, int] | None = None,
    energy: dict[str, int] | None = None,
    deep_pct: float | None = None,
    components: dict[str, int] | None = None,
    dow: dict[str, int] | None = None,
    total: int = 10,
) -> AggregatedWindow:
    return AggregatedWindow(
        window_start=datetime.date(2026, 6, 1),
        window_end=datetime.date(2026, 6, 7),
        total_observations=total,
        by_type=types or {"action": total},
        by_project=projects or {"PRJ-001": total},
        by_energy=energy or {"high": total},
        deep_work_pct=deep_pct,
        by_source_component=components or {"cli": total},
        by_day_of_week=dow or {"monday": total},
    )


# ---------------------------------------------------------------------------
# 1. BehavioralBiasDetector
# ---------------------------------------------------------------------------


class TestBehavioralBiasDetector:
    def test_no_bias_when_attention_matches_weights(self):
        detector = BehavioralBiasDetector()
        windows = [
            _win(projects={"A": 5, "B": 5}),
            _win(projects={"A": 6, "B": 4}),
            _win(projects={"A": 5, "B": 5}),
        ]
        pairs = [ProjectPriorityPair("A", "B", 0.5, 0.5)]
        results = detector.detect(windows, pairs, 0)
        assert results == []

    def test_bias_detected_when_attention_diverges(self):
        detector = BehavioralBiasDetector()
        windows = [
            _win(projects={"A": 9, "B": 1}),
            _win(projects={"A": 8, "B": 2}),
            _win(projects={"A": 10, "B": 0}),
        ]
        pairs = [ProjectPriorityPair("A", "B", 0.5, 0.5)]
        results = detector.detect(windows, pairs, 0)
        assert len(results) == 1
        assert results[0].pattern_type == PatternType.BEHAVIORAL_BIAS

    def test_not_enough_windows(self):
        detector = BehavioralBiasDetector()
        windows = [
            _win(projects={"A": 9, "B": 1}),
        ]
        pairs = [ProjectPriorityPair("A", "B", 0.5, 0.5)]
        results = detector.detect(windows, pairs, 0)
        assert results == []


# ---------------------------------------------------------------------------
# 2. CyclicalPatternDetector
# ---------------------------------------------------------------------------


class TestCyclicalPatternDetector:
    def test_cyclical_detected(self):
        detector = CyclicalPatternDetector()
        windows = [
            _win(types={"planning": 5, "coding": 1}, dow={"monday": 6}, total=6),
            _win(types={"planning": 4, "review": 2}, dow={"monday": 6}, total=6),
            _win(types={"planning": 6}, dow={"monday": 6}, total=6),
        ]
        results = detector.detect(
            windows,
            {"planning": "Planning", "coding": "Development"},
            0,
        )
        assert len(results) == 1
        assert results[0].pattern_type == PatternType.CYCLICAL_PATTERN

    def test_cyclical_not_detected_when_random(self):
        detector = CyclicalPatternDetector()
        windows = [
            _win(types={"planning": 3, "coding": 3}, dow={"monday": 6}, total=6),
            _win(types={"review": 3, "coding": 3}, dow={"tuesday": 6}, total=6),
        ]
        results = detector.detect(
            windows,
            {"planning": "Planning", "coding": "Development", "review": "Review"},
            0,
        )
        assert len(results) == 0

    def test_no_windows(self):
        detector = CyclicalPatternDetector()
        results = detector.detect([], {}, 0)
        assert results == []


# ---------------------------------------------------------------------------
# 3. AttentionCliffDetector
# ---------------------------------------------------------------------------


class TestAttentionCliffDetector:
    def test_cliff_detected(self):
        detector = AttentionCliffDetector(drop_threshold=0.8)
        windows = [
            _win(projects={"PRJ-001": 10}),
            _win(projects={"PRJ-001": 0}),
            _win(projects={"PRJ-001": 0}),
        ]
        results = detector.detect(windows, 0)
        assert len(results) == 1
        assert results[0].pattern_type == PatternType.ATTENTION_CLIFF

    def test_cliff_not_detected_when_gradual(self):
        detector = AttentionCliffDetector(drop_threshold=0.8)
        windows = [
            _win(projects={"PRJ-001": 10}),
            _win(projects={"PRJ-001": 5}),
            _win(projects={"PRJ-001": 2}),
        ]
        results = detector.detect(windows, 0)
        assert results == []

    def test_cliff_not_detected_when_recovered(self):
        detector = AttentionCliffDetector(drop_threshold=0.8)
        windows = [
            _win(projects={"PRJ-001": 10}),
            _win(projects={"PRJ-001": 0}),
            _win(projects={"PRJ-001": 8}),
        ]
        results = detector.detect(windows, 0)
        assert results == []

    def test_not_enough_windows(self):
        detector = AttentionCliffDetector(min_windows=3)
        windows = [
            _win(projects={"PRJ-001": 10}),
            _win(projects={"PRJ-001": 0}),
        ]
        results = detector.detect(windows, 0)
        assert results == []


# ---------------------------------------------------------------------------
# 4. DelegationPatternDetector
# ---------------------------------------------------------------------------


class TestDelegationPatternDetector:
    def test_delegation_detected(self):
        detector = DelegationPatternDetector()
        windows = [
            _win(projects={"PRJ-001": 1, "PRJ-002": 1}, total=20),
            _win(projects={"PRJ-001": 1, "PRJ-002": 1}, total=20),
            _win(projects={"PRJ-001": 1, "PRJ-002": 1}, total=20),
        ]
        assignments = [
            CategoryAssignment("PRJ-001", "infrastructure"),
            CategoryAssignment("PRJ-002", "infrastructure"),
        ]
        results = detector.detect(
            windows, assignments, {"infrastructure": 0.5}, 0
        )
        # infrastructure: expected 0.5, actual ~0.1 across windows -> below 50% of expected
        assert len(results) == 1
        assert results[0].pattern_type == PatternType.DELEGATION_PATTERN

    def test_no_delegation_when_on_target(self):
        detector = DelegationPatternDetector()
        windows = [
            _win(projects={"PRJ-001": 5, "PRJ-002": 5}, total=20),
            _win(projects={"PRJ-001": 5, "PRJ-002": 5}, total=20),
            _win(projects={"PRJ-001": 5, "PRJ-002": 5}, total=20),
        ]
        assignments = [
            CategoryAssignment("PRJ-001", "infrastructure"),
            CategoryAssignment("PRJ-002", "infrastructure"),
        ]
        results = detector.detect(
            windows, assignments, {"infrastructure": 0.5}, 0
        )
        assert results == []


# ---------------------------------------------------------------------------
# 5. EnergyCorrelationDetector
# ---------------------------------------------------------------------------


class TestEnergyCorrelationDetector:
    def test_correlation_detected(self):
        detector = EnergyCorrelationDetector(min_occurrences=3)
        obs = [
            _obs(type="coding", energy="high"),
            _obs(type="coding", energy="high"),
            _obs(type="coding", energy="high"),
            _obs(type="coding", energy="medium"),
        ]
        windows = [_win(total=4)]
        results = detector.detect(windows, obs, 0)
        assert len(results) == 1
        assert results[0].pattern_type == PatternType.ENERGY_CORRELATION

    def test_no_correlation_when_evenly_split(self):
        detector = EnergyCorrelationDetector(min_occurrences=3)
        obs = [
            _obs(type="meeting", energy="high"),
            _obs(type="meeting", energy="medium"),
            _obs(type="meeting", energy="low"),
            _obs(type="meeting", energy="high"),
        ]
        windows = [_win(total=4)]
        results = detector.detect(windows, obs, 0)
        assert results == []

    def test_below_min_occurrences(self):
        detector = EnergyCorrelationDetector(min_occurrences=5)
        obs = [_obs(type="coding", energy="high") for _ in range(3)]
        windows = [_win(total=3)]
        results = detector.detect(windows, obs, 0)
        assert results == []


# ---------------------------------------------------------------------------
# 6. CompletionSignatureDetector
# ---------------------------------------------------------------------------


class TestCompletionSignatureDetector:
    def test_signature_detected(self):
        detector = CompletionSignatureDetector()
        completed = [
            ("PRJ-001", [_win(types={"planning": 3, "coding": 5, "review": 2})]),
            ("PRJ-002", [_win(types={"planning": 4, "coding": 6, "testing": 1})]),
        ]
        abandoned = [
            ("PRJ-003", [_win(types={"coding": 10})]),
            ("PRJ-004", [_win(types={"research": 8, "coding": 2})]),
        ]
        results = detector.detect(completed, abandoned, 0)
        # "planning" appears in all completed, never in abandoned
        assert len(results) == 1
        assert "planning" in results[0].description

    def test_no_signature_when_no_completed(self):
        detector = CompletionSignatureDetector()
        results = detector.detect([], [("PRJ-003", [_win()])], 0)
        assert results == []

    def test_no_signature_when_no_abandoned(self):
        detector = CompletionSignatureDetector()
        results = detector.detect([("PRJ-001", [_win()])], [], 0)
        assert results == []


# ---------------------------------------------------------------------------
# 7. RejectionPatternDetector
# ---------------------------------------------------------------------------


class TestRejectionPatternDetector:
    def test_rejection_detected(self):
        detector = RejectionPatternDetector()
        today = datetime.date.today()
        history = {
            "preference_divergence": [
                today - datetime.timedelta(days=d) for d in [5, 10, 15]
            ]
        }
        results = detector.detect(history, 0)
        assert len(results) == 1
        assert results[0].pattern_type == PatternType.REJECTION_PATTERN

    def test_no_rejection_when_few_rejections(self):
        detector = RejectionPatternDetector()
        today = datetime.date.today()
        history = {
            "preference_divergence": [
                today - datetime.timedelta(days=d) for d in [5]
            ]
        }
        results = detector.detect(history, 0)
        assert results == []

    def test_no_history(self):
        detector = RejectionPatternDetector()
        results = detector.detect({}, 0)
        assert results == []
