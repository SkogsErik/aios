"""
learning_engine.py — Layer 2 learning engine (ADR-011).

Five-stage pipeline:
  1. Aggregation — raw observations into temporal windows
  2. Pattern detection — compare aggregates across windows
  3. Reconciliation — compare patterns against declared persona values
  4. Confidence scoring — deterministic confidence formula
  5. Candidate generation — format patterns for operator review

All outputs are derived (Principle 7). No output modifies the canonical
persona without operator approval.
"""

import datetime
import enum
import math
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class Observation(NamedTuple):
    id: str
    timestamp: datetime.datetime
    type: str  # action | decision | event | note | completion
    source_mechanism: str  # auto | manual | scheduled
    source_component: str  # workflow | gateway | calendar | cli | ...
    summary: str
    project: str | None
    energy: str | None  # high | medium | low
    tags: list[str]


class DeclaredValue(NamedTuple):
    attribute: str          # e.g. "deep_work_weight"
    value: float            # e.g. 0.8
    weight: float           # 0.0–1.0 how important this value is to the operator


class AggregatedWindow(NamedTuple):
    window_start: datetime.date
    window_end: datetime.date
    total_observations: int
    by_type: dict[str, int]
    by_project: dict[str, int]
    by_energy: dict[str, int]
    deep_work_pct: float | None  # % of observations tagged as deep work


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


class ObservationAggregator:
    def aggregate(
        self,
        observations: list[Observation],
        window_start: datetime.date,
        window_end: datetime.date,
        deep_work_tags: frozenset[str] | None = None,
    ) -> AggregatedWindow:
        if deep_work_tags is None:
            deep_work_tags = frozenset({"deep_work", "focus", "coding", "writing"})

        by_type: dict[str, int] = {}
        by_project: dict[str, int] = {}
        by_energy: dict[str, int] = {}
        deep_work_count = 0

        for obs in observations:
            by_type[obs.type] = by_type.get(obs.type, 0) + 1
            if obs.project:
                by_project[obs.project] = by_project.get(obs.project, 0) + 1
            if obs.energy:
                by_energy[obs.energy] = by_energy.get(obs.energy, 0) + 1
            if deep_work_tags.intersection(obs.tags):
                deep_work_count += 1

        total = len(observations)
        deep_work_pct = (deep_work_count / total) if total > 0 else None

        return AggregatedWindow(
            window_start=window_start,
            window_end=window_end,
            total_observations=total,
            by_type=by_type,
            by_project=by_project,
            by_energy=by_energy,
            deep_work_pct=deep_work_pct,
        )


# ---------------------------------------------------------------------------
# Confidence scoring (deterministic)
# ---------------------------------------------------------------------------


class ConfidenceScorer:
    def score(
        self,
        base_rate: float,
        consistency: float,
        recency: float,
        specificity: float,
        feedback_history: float,
    ) -> float:
        raw = (
            0.3 * base_rate
            + 0.3 * consistency
            + 0.2 * recency
            + 0.1 * specificity
            + 0.1 * feedback_history
        )
        return max(0.0, min(1.0, raw))

    def compute_recency(
        self, windows_since_last_support: int, decay_lambda: float = 0.5
    ) -> float:
        return min(1.0, math.exp(-decay_lambda * windows_since_last_support))

    def compute_feedback_history(
        self, acceptances: int, rejections: int, total_reviews: int
    ) -> float:
        if total_reviews == 0:
            return 0.0
        return (acceptances - rejections) / total_reviews


# ---------------------------------------------------------------------------
# Pattern types and lifecycle
# ---------------------------------------------------------------------------


class PatternType(enum.Enum):
    PREFERENCE_DIVERGENCE = "preference_divergence"
    BEHAVIORAL_BIAS = "behavioral_bias"
    CYCLICAL_PATTERN = "cyclical"
    ATTENTION_CLIFF = "attention_cliff"
    DELEGATION_PATTERN = "delegation"
    ENERGY_CORRELATION = "energy_correlation"
    COMPLETION_SIGNATURE = "completion_signature"
    REJECTION_PATTERN = "rejection_pattern"


class PatternStatus(enum.Enum):
    DETECTED = "detected"
    CANDIDATE = "candidate"
    SURFACED = "surfaced"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"

    def __str__(self) -> str:
        return self.value


class FeedbackAction(enum.Enum):
    ACCEPTED = "accepted"
    ACCEPTED_MODIFIED = "accepted_modified"
    REJECTED = "rejected"
    REJECTED_WITH_REASON = "rejected_with_reason"
    DISMISSED = "dismissed"
    SNOOZED = "snoozed"


class PatternCandidate(NamedTuple):
    id: str
    pattern_type: PatternType
    confidence: float
    title: str
    description: str
    evidence: list[AggregatedWindow]
    suggestions: list[str]
    status: PatternStatus
    requires_review: bool
    detection_count: int


# ---------------------------------------------------------------------------
# Preference reconciliation
# ---------------------------------------------------------------------------


class Tension(NamedTuple):
    attribute: str
    declared_value: float
    observed_value: float
    magnitude: float
    threshold: float
    severity: str  # minor | moderate | critical


class PreferenceReconciler:
    def __init__(self, divergence_threshold: float = 0.3) -> None:
        self._threshold = divergence_threshold

    def reconcile(
        self,
        declared_values: list[DeclaredValue],
        aggregated: AggregatedWindow,
    ) -> list[Tension]:
        tensions: list[Tension] = []
        for dv in declared_values:
            observed = self._extract_observed(dv.attribute, aggregated)
            if observed is None:
                continue
            magnitude = abs(dv.value - observed)
            if magnitude >= self._threshold:
                severity = self._classify_severity(magnitude)
                tensions.append(
                    Tension(
                        attribute=dv.attribute,
                        declared_value=dv.value,
                        observed_value=observed,
                        magnitude=magnitude,
                        threshold=self._threshold,
                        severity=severity,
                    )
                )
        return tensions

    @staticmethod
    def _classify_severity(magnitude: float) -> str:
        if magnitude >= 0.5:
            return "critical"
        if magnitude >= 0.3:
            return "moderate"
        return "minor"

    @staticmethod
    def _extract_observed(
        attribute: str, aggregated: AggregatedWindow
    ) -> float | None:
        if attribute == "deep_work_weight":
            return aggregated.deep_work_pct
        return None


# ---------------------------------------------------------------------------
# Learning engine (full pipeline)
# ---------------------------------------------------------------------------


class LearningEngine:
    def __init__(self) -> None:
        self._aggregator = ObservationAggregator()
        self._reconciler = PreferenceReconciler(divergence_threshold=0.3)
        self._confidence_scorer = ConfidenceScorer()

    def run_aggregation(
        self,
        observations: list[Observation],
        window_start: datetime.date,
        window_end: datetime.date,
    ) -> AggregatedWindow:
        return self._aggregator.aggregate(observations, window_start, window_end)

    def reconcile(
        self,
        declared_values: list[DeclaredValue],
        aggregated: AggregatedWindow,
    ) -> list[Tension]:
        return self._reconciler.reconcile(declared_values, aggregated)

    def generate_candidates(
        self,
        tensions: list[Tension],
        windows: list[AggregatedWindow],
        feedback_history: dict[str, tuple[int, int]],  # pattern_type -> (accepts, rejects)
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        candidates: list[PatternCandidate] = []
        for tension in tensions:
            base_rate = min(1.0, len(windows) / 5.0)
            consistency = self._compute_consistency(tension, windows)
            recency = self._confidence_scorer.compute_recency(0)
            specificity = 0.7 if tension.severity == "critical" else 0.4
            accepts, rejects = feedback_history.get(tension.attribute, (0, 0))
            feedback = self._confidence_scorer.compute_feedback_history(
                accepts, rejects, accepts + rejects
            )
            confidence = self._confidence_scorer.score(
                base_rate, consistency, recency, specificity, feedback
            )
            if confidence < 0.4:
                continue
            pattern_counter += 1
            candidates.append(
                PatternCandidate(
                    id=f"CND-{pattern_counter:04d}",
                    pattern_type=PatternType.PREFERENCE_DIVERGENCE,
                    confidence=confidence,
                    title=f"{tension.attribute}: declared vs observed divergence",
                    description=(
                        f"Declared '{tension.attribute}' = {tension.declared_value}, "
                        f"observed = {tension.observed_value:.2f} "
                        f"(magnitude: {tension.magnitude:.2f}, severity: {tension.severity})"
                    ),
                    evidence=windows[-3:],
                    suggestions=self._generate_suggestions(tension),
                    status=PatternStatus.CANDIDATE,
                    requires_review=True,
                    detection_count=1,
                )
            )
        return candidates, pattern_counter

    @staticmethod
    def _compute_consistency(
        tension: Tension, windows: list[AggregatedWindow]
    ) -> float:
        if len(windows) < 2:
            return 0.0
        consistent_count = 0
        for w in windows:
            observed = PreferenceReconciler._extract_observed(tension.attribute, w)
            if observed is not None and abs(tension.declared_value - observed) >= tension.threshold:
                consistent_count += 1
        return consistent_count / len(windows)

    @staticmethod
    def _generate_suggestions(tension: Tension) -> list[str]:
        if tension.attribute == "deep_work_weight":
            return [
                "Block daily deep work time during highest energy period",
                "Review meeting load and decline non-essential meetings",
                f"Consider updating 'deep_work_weight' from {tension.declared_value} to reflect actual allocation",
            ]
        return ["Review this value and adjust either behavior or declaration"]


# ---------------------------------------------------------------------------
# Feedback integration
# ---------------------------------------------------------------------------


class FeedbackProcessor:
    def __init__(
        self, max_rejections_before_archive: int = 3, archive_window_days: int = 30
    ) -> None:
        self._max_rejections = max_rejections_before_archive
        self._archive_window = archive_window_days

    def process(
        self,
        candidate: PatternCandidate,
        action: FeedbackAction,
        feedback_history: dict[str, list[datetime.date]],
    ) -> tuple[float, bool]:
        key = candidate.pattern_type.value
        if key not in feedback_history:
            feedback_history[key] = []

        if action == FeedbackAction.ACCEPTED:
            return 0.1, False
        if action == FeedbackAction.ACCEPTED_MODIFIED:
            return 0.05, False
        if action == FeedbackAction.REJECTED:
            feedback_history[key].append(datetime.date.today())
            rejections = [
                d
                for d in feedback_history[key]
                if (datetime.date.today() - d).days <= self._archive_window
            ]
            if len(rejections) >= self._max_rejections:
                return -0.3, True  # auto-archive
            return -0.2, False
        if action == FeedbackAction.REJECTED_WITH_REASON:
            feedback_history[key].append(datetime.date.today())
            rejections = [
                d
                for d in feedback_history[key]
                if (datetime.date.today() - d).days <= self._archive_window
            ]
            if len(rejections) >= self._max_rejections:
                return -0.3, True
            return -0.3, False
        if action == FeedbackAction.DISMISSED:
            return -0.05, False
        if action == FeedbackAction.SNOOZED:
            return 0.0, False
        return 0.0, False


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


class Prediction(NamedTuple):
    id: str
    target: str
    confidence: float
    source_pattern_id: str
    window_start: datetime.date
    window_end: datetime.date
    outcome: str | None  # null | confirmed | refuted


class PredictionEvaluator:
    @staticmethod
    def evaluate(
        prediction: Prediction,
        observations_in_window: list[Observation],
    ) -> tuple[str, float]:
        if prediction.outcome is not None:
            return prediction.outcome, 0.0
        confirmed_keywords = {"completed", "finished", "delivered", "done"}
        refuted_keywords = {"abandoned", "cancelled", "postponed", "deprioritized"}
        for obs in observations_in_window:
            words = set(obs.summary.lower().split())
            if words & confirmed_keywords:
                return "confirmed", 0.1
            if words & refuted_keywords:
                return "refuted", -0.2
        return "ambiguous", 0.0
