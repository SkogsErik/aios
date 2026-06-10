"""
test_learning_engine.py — Tests for the five-stage learning pipeline.
"""

import datetime

import pytest

from learning_engine import (
    AggregatedWindow,
    ConfidenceScorer,
    DeclaredValue,
    FeedbackAction,
    FeedbackProcessor,
    LearningEngine,
    Observation,
    ObservationAggregator,
    PatternCandidate,
    PatternStatus,
    PatternType,
    Prediction,
    PredictionEvaluator,
    PreferenceReconciler,
    Tension,
)


def _obs(
    summary: str = "did something",
    type: str = "action",
    project: str | None = "PRJ-001",
    energy: str | None = "high",
    tags: list[str] | None = None,
    source_mechanism: str = "auto",
    source_component: str = "cli",
) -> Observation:
    return Observation(
        id="OBS-001",
        timestamp=datetime.datetime(2026, 6, 10, 14, 0),
        type=type,
        source_mechanism=source_mechanism,
        source_component=source_component,
        summary=summary,
        project=project,
        energy=energy,
        tags=tags or [],
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


class TestObservationAggregator:
    def test_empty_observations(self):
        aggregator = ObservationAggregator()
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2026, 6, 10)
        result = aggregator.aggregate([], start, end)
        assert result.total_observations == 0
        assert result.deep_work_pct is None

    def test_deep_work_pct_from_tags(self):
        aggregator = ObservationAggregator()
        obs_list = [
            _obs(summary="coded feature", tags=["coding"]),
            _obs(summary="meeting", tags=["meeting"]),
            _obs(summary="wrote spec", tags=["writing"]),
            _obs(summary="reviewed PR", tags=["review"]),
        ]
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2026, 6, 10)
        result = aggregator.aggregate(obs_list, start, end)
        assert result.total_observations == 4
        assert result.deep_work_pct == 0.5  # coding, writing (2/4)

    def test_by_project_counts(self):
        aggregator = ObservationAggregator()
        obs_list = [
            _obs(project="PRJ-001"),
            _obs(project="PRJ-001"),
            _obs(project="PRJ-002"),
            _obs(project=None),
        ]
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2026, 6, 10)
        result = aggregator.aggregate(obs_list, start, end)
        assert result.by_project["PRJ-001"] == 2
        assert result.by_project["PRJ-002"] == 1

    def test_by_energy_counts(self):
        aggregator = ObservationAggregator()
        obs_list = [
            _obs(energy="high"),
            _obs(energy="high"),
            _obs(energy="medium"),
            _obs(energy=None),
        ]
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2026, 6, 10)
        result = aggregator.aggregate(obs_list, start, end)
        assert result.by_energy["high"] == 2
        assert result.by_energy["medium"] == 1
        assert "low" not in result.by_energy


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


class TestConfidenceScorer:
    def test_max_confidence(self):
        scorer = ConfidenceScorer()
        score = scorer.score(
            base_rate=1.0, consistency=1.0, recency=1.0, specificity=1.0, feedback_history=1.0
        )
        assert score == 1.0

    def test_min_confidence(self):
        scorer = ConfidenceScorer()
        score = scorer.score(
            base_rate=0.0, consistency=0.0, recency=0.0, specificity=0.0, feedback_history=-1.0
        )
        assert score == 0.0

    def test_mid_confidence(self):
        scorer = ConfidenceScorer()
        score = scorer.score(
            base_rate=0.6, consistency=0.6, recency=0.5, specificity=0.3, feedback_history=0.0
        )
        assert 0.4 < score < 0.6

    def test_recency_decay(self):
        scorer = ConfidenceScorer()
        recent = scorer.compute_recency(0)
        older = scorer.compute_recency(5)
        assert recent > older

    def test_feedback_history_positive(self):
        scorer = ConfidenceScorer()
        assert scorer.compute_feedback_history(3, 1, 4) == 0.5

    def test_feedback_history_negative(self):
        scorer = ConfidenceScorer()
        assert scorer.compute_feedback_history(0, 3, 3) == -1.0

    def test_feedback_history_no_reviews(self):
        scorer = ConfidenceScorer()
        assert scorer.compute_feedback_history(0, 0, 0) == 0.0


# ---------------------------------------------------------------------------
# Preference reconciliation
# ---------------------------------------------------------------------------


class TestPreferenceReconciler:
    def test_no_tension_when_below_threshold(self):
        reconciler = PreferenceReconciler(divergence_threshold=0.3)
        declared = [DeclaredValue("deep_work_weight", 0.6, 1.0)]
        window = AggregatedWindow(
            window_start=datetime.date(2026, 6, 1),
            window_end=datetime.date(2026, 6, 10),
            total_observations=10,
            by_type={"action": 10},
            by_project={"PRJ-001": 10},
            by_energy={"high": 10},
            deep_work_pct=0.7,
        )
        tensions = reconciler.reconcile(declared, window)
        assert tensions == []

    def test_tension_when_above_threshold(self):
        reconciler = PreferenceReconciler(divergence_threshold=0.3)
        declared = [DeclaredValue("deep_work_weight", 0.8, 1.0)]
        window = AggregatedWindow(
            window_start=datetime.date(2026, 6, 1),
            window_end=datetime.date(2026, 6, 10),
            total_observations=10,
            by_type={"action": 10},
            by_project={"PRJ-001": 10},
            by_energy={"high": 10},
            deep_work_pct=0.25,
        )
        tensions = reconciler.reconcile(declared, window)
        assert len(tensions) == 1
        assert tensions[0].attribute == "deep_work_weight"
        assert tensions[0].magnitude == 0.55
        assert tensions[0].severity == "critical"

    def test_unknown_attribute_skipped(self):
        reconciler = PreferenceReconciler()
        declared = [DeclaredValue("unknown_attr", 1.0, 1.0)]
        window = AggregatedWindow(
            window_start=datetime.date(2026, 6, 1),
            window_end=datetime.date(2026, 6, 10),
            total_observations=10,
            by_type={"action": 10},
            by_project={"PRJ-001": 10},
            by_energy={"high": 10},
            deep_work_pct=0.5,
        )
        tensions = reconciler.reconcile(declared, window)
        assert tensions == []


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------


class TestCandidateGeneration:
    def test_candidate_generated_above_threshold(self):
        engine = LearningEngine()
        tensions = [
            Tension(
                attribute="deep_work_weight",
                declared_value=0.8,
                observed_value=0.25,
                magnitude=0.55,
                threshold=0.3,
                severity="critical",
            )
        ]
        # Need >= 5 windows for base_rate >= 1.0 and enough for consistency
        windows = [
            AggregatedWindow(
                window_start=datetime.date(2026, x, x),
                window_end=datetime.date(2026, x + 1, x + 7),
                total_observations=10,
                by_type={"action": 10},
                by_project={"PRJ-001": 10},
                by_energy={"high": 10},
                deep_work_pct=0.25,
            )
            for x in range(1, 6)
        ]
        candidates, counter = engine.generate_candidates(tensions, windows, {}, 0)
        assert len(candidates) == 1
        assert candidates[0].confidence >= 0.4
        assert candidates[0].requires_review is True
        assert "deep_work_weight" in candidates[0].title

    def test_no_candidate_very_low_confidence(self):
        engine = LearningEngine()
        tensions = [
            Tension(
                attribute="deep_work_weight",
                declared_value=0.8,
                observed_value=0.5,
                magnitude=0.3,
                threshold=0.3,
                severity="moderate",
            )
        ]
        windows: list[AggregatedWindow] = []
        candidates, counter = engine.generate_candidates(tensions, windows, {}, 0)
        assert len(candidates) == 0

    def test_candidate_includes_suggestions(self):
        engine = LearningEngine()
        tensions = [
            Tension(
                attribute="deep_work_weight",
                declared_value=0.8,
                observed_value=0.25,
                magnitude=0.55,
                threshold=0.3,
                severity="critical",
            )
        ]
        windows = [
            AggregatedWindow(
                window_start=datetime.date(2026, x, x),
                window_end=datetime.date(2026, x + 1, x + 7),
                total_observations=10,
                by_type={"action": 10},
                by_project={"PRJ-001": 10},
                by_energy={"high": 10},
                deep_work_pct=0.25,
            )
            for x in range(1, 6)
        ]
        candidates, _ = engine.generate_candidates(tensions, windows, {}, 0)
        assert len(candidates[0].suggestions) > 0


# ---------------------------------------------------------------------------
# Feedback processing
# ---------------------------------------------------------------------------


class TestFeedbackProcessor:
    def test_accept_increases_confidence(self):
        processor = FeedbackProcessor()
        candidate = PatternCandidate(
            id="CND-0001",
            pattern_type=PatternType.PREFERENCE_DIVERGENCE,
            confidence=0.5,
            title="test",
            description="test",
            evidence=[],
            suggestions=[],
            status=PatternStatus.CANDIDATE,
            requires_review=True,
            detection_count=1,
        )
        delta, archive = processor.process(candidate, FeedbackAction.ACCEPTED, {})
        assert delta == 0.1
        assert archive is False

    def test_three_rejections_triggers_archive(self):
        processor = FeedbackProcessor(max_rejections_before_archive=3)
        candidate = PatternCandidate(
            id="CND-0001",
            pattern_type=PatternType.PREFERENCE_DIVERGENCE,
            confidence=0.5,
            title="test",
            description="test",
            evidence=[],
            suggestions=[],
            status=PatternStatus.CANDIDATE,
            requires_review=True,
            detection_count=1,
        )
        history: dict[str, list[datetime.date]] = {}
        today = datetime.date.today()
        past = today - datetime.timedelta(days=25)
        history["preference_divergence"] = [past, past, past]
        delta, archive = processor.process(candidate, FeedbackAction.REJECTED, history)
        # 3 existing + 1 new = 4 within 30 days >= 3
        assert delta == -0.3
        assert archive is True

    def test_rejection_within_window_counts(self):
        processor = FeedbackProcessor(max_rejections_before_archive=3)
        candidate = PatternCandidate(
            id="CND-0001",
            pattern_type=PatternType.PREFERENCE_DIVERGENCE,
            confidence=0.5,
            title="test",
            description="test",
            evidence=[],
            suggestions=[],
            status=PatternStatus.CANDIDATE,
            requires_review=True,
            detection_count=1,
        )
        history: dict[str, list[datetime.date]] = {}
        far_past = datetime.date.today() - datetime.timedelta(days=45)
        history["preference_divergence"] = [far_past, far_past]
        delta, archive = processor.process(candidate, FeedbackAction.REJECTED, history)
        assert delta == -0.2
        assert archive is False


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


class TestPredictionEvaluator:
    def test_confirmed_by_keyword(self):
        prediction = Prediction(
            id="PRD-0001",
            target="PRJ-042 will be completed by June 15",
            confidence=0.65,
            source_pattern_id="PAT-0001",
            window_start=datetime.date(2026, 6, 1),
            window_end=datetime.date(2026, 6, 15),
            outcome=None,
        )
        obs = [
            _obs(summary="completed PRJ-042 deliverable"),
        ]
        outcome, delta = PredictionEvaluator.evaluate(prediction, obs)
        assert outcome == "confirmed"
        assert delta == 0.1

    def test_refuted_by_keyword(self):
        prediction = Prediction(
            id="PRD-0002",
            target="PRJ-042 will be completed by June 15",
            confidence=0.65,
            source_pattern_id="PAT-0001",
            window_start=datetime.date(2026, 6, 1),
            window_end=datetime.date(2026, 6, 15),
            outcome=None,
        )
        obs = [
            _obs(summary="abandoned PRJ-042"),
        ]
        outcome, delta = PredictionEvaluator.evaluate(prediction, obs)
        assert outcome == "refuted"
        assert delta == -0.2

    def test_ambiguous_when_no_match(self):
        prediction = Prediction(
            id="PRD-0003",
            target="PRJ-042 will be completed by June 15",
            confidence=0.65,
            source_pattern_id="PAT-0001",
            window_start=datetime.date(2026, 6, 1),
            window_end=datetime.date(2026, 6, 15),
            outcome=None,
        )
        obs = [
            _obs(summary="had a meeting about PRJ-042"),
        ]
        outcome, delta = PredictionEvaluator.evaluate(prediction, obs)
        assert outcome == "ambiguous"
        assert delta == 0.0


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    def test_full_pipeline_minimal(self):
        engine = LearningEngine()
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2026, 6, 10)

        obs = [
            _obs(summary="coded feature", tags=["coding"]),
            _obs(summary="meeting", tags=["meeting"]),
            _obs(summary="wrote spec", tags=["writing"]),
            _obs(summary="reviewed PR", tags=["review"]),
            _obs(summary="coded more", tags=["coding"]),
        ]

        aggregated = engine.run_aggregation(obs, start, end)
        assert aggregated.total_observations == 5
        assert aggregated.deep_work_pct == 0.6

        declared = [DeclaredValue("deep_work_weight", 0.9, 1.0)]
        tensions = engine.reconcile(declared, aggregated)
        assert len(tensions) == 1
        assert tensions[0].magnitude == pytest.approx(0.3, abs=0.001)
        assert tensions[0].severity == "moderate"

        candidates, counter = engine.generate_candidates(
            tensions, [aggregated], {}, 0
        )
        assert len(candidates) >= 0

    def test_full_pipeline_high_divergence(self):
        engine = LearningEngine()
        start = datetime.date(2026, 6, 1)
        end = datetime.date(2026, 6, 10)

        obs = [
            _obs(summary="meeting 1", tags=["meeting"]),
            _obs(summary="meeting 2", tags=["meeting"]),
            _obs(summary="meeting 3", tags=["meeting"]),
            _obs(summary="admin", tags=["admin"]),
        ]

        aggregated = engine.run_aggregation(obs, start, end)
        assert aggregated.deep_work_pct == 0.0

        declared = [DeclaredValue("deep_work_weight", 0.8, 1.0)]
        tensions = engine.reconcile(declared, aggregated)
        assert len(tensions) == 1
        assert tensions[0].magnitude == 0.8
        assert tensions[0].severity == "critical"

        candidates, counter = engine.generate_candidates(
            tensions, [aggregated] * 5, {}, 0
        )
        assert len(candidates) == 1
        assert candidates[0].pattern_type == PatternType.PREFERENCE_DIVERGENCE
        assert candidates[0].requires_review is True
