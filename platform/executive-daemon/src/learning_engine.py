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
    by_source_component: dict[str, int] | None = None  # component -> count
    by_day_of_week: dict[str, int] | None = None  # monday -> count, etc.


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
        by_source_component: dict[str, int] = {}
        by_day_of_week: dict[str, int] = {}
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        deep_work_count = 0

        for obs in observations:
            by_type[obs.type] = by_type.get(obs.type, 0) + 1
            if obs.project:
                by_project[obs.project] = by_project.get(obs.project, 0) + 1
            if obs.energy:
                by_energy[obs.energy] = by_energy.get(obs.energy, 0) + 1
            by_source_component[obs.source_component] = (
                by_source_component.get(obs.source_component, 0) + 1
            )
            dow = day_names[obs.timestamp.weekday()]
            by_day_of_week[dow] = by_day_of_week.get(dow, 0) + 1
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
            by_source_component=by_source_component,
            by_day_of_week=by_day_of_week,
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


_PREDICTION_WINDOW_DAYS = 7


def generate_predictions(
    candidates: list[PatternCandidate],
    prediction_counter: int,
    window_days: int = _PREDICTION_WINDOW_DAYS,
) -> tuple[list[Prediction], int]:
    """Generate predictions from pattern candidates.

    For each candidate above the medium confidence threshold (>= 0.4),
    a Prediction is created with a configurable future window. The prediction
    target is derived from the candidate's title and suggestions.

    Returns (predictions, updated_counter).
    """
    predictions: list[Prediction] = []
    today = datetime.date.today()
    for candidate in candidates:
        if candidate.confidence < 0.4:
            continue
        prediction_counter += 1
        predictions.append(
            Prediction(
                id=f"PRD-{prediction_counter:04d}",
                target=_derive_target(candidate),
                confidence=candidate.confidence,
                source_pattern_id=candidate.id,
                window_start=today,
                window_end=today + datetime.timedelta(days=window_days),
                outcome=None,
            )
        )
    return predictions, prediction_counter


def _derive_target(candidate: PatternCandidate) -> str:
    """Derive a prediction target from a pattern candidate."""
    if candidate.pattern_type == PatternType.PREFERENCE_DIVERGENCE:
        attr = candidate.description.split("'")[1] if "'" in candidate.description else "unknown"
        return f"Will adjust {attr} to reduce divergence within the prediction window"
    if candidate.pattern_type == PatternType.BEHAVIORAL_BIAS:
        return "Attention allocation will shift toward declared priorities"
    if candidate.pattern_type == PatternType.ATTENTION_CLIFF:
        proj = candidate.title.replace("Attention cliff: ", "")
        return f"Will resume attention on {proj} within the prediction window"
    if candidate.pattern_type == PatternType.ENERGY_CORRELATION:
        return "Activity-energy correlation will persist across the prediction window"
    if candidate.pattern_type == PatternType.COMPLETION_SIGNATURE:
        return "New projects will follow the completion signature pattern"
    if candidate.pattern_type == PatternType.REJECTION_PATTERN:
        return f"Rejection rate for '{candidate.title}' will remain above threshold"
    if candidate.pattern_type == PatternType.CYCLICAL_PATTERN:
        return "Weekly activity patterns will remain consistent within the prediction window"
    if candidate.pattern_type == PatternType.DELEGATION_PATTERN:
        return "Delegation imbalance will continue without intervention"
    return f"Pattern '{candidate.title}' will persist"


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


class PredictionEvaluationResult(NamedTuple):
    prediction_id: str
    outcome: str
    confidence_delta: float


# ---------------------------------------------------------------------------
# AI inference runner (Phase 7 — ADR-011 Layer 2)
# ---------------------------------------------------------------------------


class AiInferenceRunner:
    """Scheduled AI inference for pattern detection and reconciliation.

    Calls the model gateway with aggregated observation windows to detect
    complex patterns that deterministic rules cannot catch. This is
    Layer 2 of the executive reasoning engine (ADR-011).

    The runner is scheduled separately from deterministic pattern detection.
    It degrades gracefully when the model gateway is unavailable.
    """

    def __init__(self, gateway=None) -> None:
        self._gateway = gateway

    def analyse(
        self,
        windows: list[AggregatedWindow],
        window_labels: list[str],
        declared_values: list[DeclaredValue] | None = None,
    ) -> str:
        """Analyse aggregated windows and return AI-generated insights.

        Parameters
        ----------
        windows : list[AggregatedWindow]
            Temporal aggregation windows to analyse.
        window_labels : list[str]
            Human-readable labels for each window (e.g. "Week 1", "Week 2").
        declared_values : list[DeclaredValue], optional
            Declared persona values for reconciliation context.

        Returns
        -------
        str
            AI-generated analysis text, or error message if gateway unavailable.
        """
        if len(windows) < 2:
            return "Insufficient windows for AI inference (need at least 2)."

        prompt = self._build_prompt(windows, window_labels, declared_values)
        try:
            response = self._call_gateway(prompt)
            return response
        except Exception as e:
            return f"AI inference skipped: {e}"

    def _build_prompt(
        self,
        windows: list[AggregatedWindow],
        window_labels: list[str],
        declared_values: list[DeclaredValue] | None,
    ) -> str:
        lines = [
            "You are an AI inference engine for a personal cognitive system called AIOS.",
            "Analyse the aggregated observation windows below and identify:",
            "",
            "1. BEHAVIORAL PATTERNS: Any recurring patterns in activity type, energy levels,",
            "   project attention, or work habits across windows.",
            "2. PREFERENCE DIVERGENCE: Where observed behaviour may differ from declared values.",
            "3. PREDICTIONS: What you predict will happen in the next window based on trends.",
            "4. ANOMALIES: Any windows that stand out as significantly different.",
            "",
            "Be specific and reference actual numbers from the data.",
            "Format your response as bullet points under each category.",
            "",
        ]

        for i, (w, label) in enumerate(zip(windows, window_labels)):
            lines.append(f"--- {label} ---")
            lines.append(f"  Total observations: {w.total_observations}")
            lines.append(f"  By type: {dict(w.by_type)}")
            lines.append(f"  By project: {dict(w.by_project)}")
            lines.append(f"  By energy: {dict(w.by_energy)}")
            if w.deep_work_pct is not None:
                lines.append(f"  Deep work %: {w.deep_work_pct:.0%}")
            if w.by_source_component:
                lines.append(f"  By source: {dict(w.by_source_component)}")
            if w.by_day_of_week:
                lines.append(f"  By day of week: {dict(w.by_day_of_week)}")
            lines.append("")

        if declared_values:
            lines.append("--- Declared Persona Values ---")
            for dv in declared_values:
                lines.append(f"  {dv.attribute}: {dv.value} (weight: {dv.weight})")
            lines.append("")

        lines.append(
            "Provide your analysis. For each pattern or divergence, estimate a confidence level (0.0-1.0)."
        )
        return "\n".join(lines)

    def _call_gateway(self, prompt: str) -> str:
        if self._gateway is None:
            import sys
            from pathlib import Path

            _ROOT = Path(__file__).resolve().parent.parent.parent.parent
            _GW_SRC = _ROOT / "platform" / "model-gateway" / "src"
            if str(_GW_SRC) not in sys.path:
                sys.path.insert(0, str(_GW_SRC))
            from gateway import complete as _call
        else:
            _call = self._gateway.complete

        response = _call(
            prompt,
            caller_id="executive-daemon.learning_engine.ai_inference",
            context={"purpose": "ai_inference", "windows": len(prompt)},
        )
        return response.content


class PredictionScheduler:
    """Cron-like scheduler that evaluates expired predictions.

    On each tick it queries the PredictionStore for predictions whose
    ``window_end`` is in the past and whose ``outcome`` is still ``None``,
    fetches actual observations for that window, runs
    ``PredictionEvaluator.evaluate``, and persists the result.
    """

    def __init__(
        self,
        prediction_store: object,
        observation_store: object,
    ) -> None:
        self._prediction_store = prediction_store
        self._observation_store = observation_store
        self._evaluator = PredictionEvaluator()

    def tick(self) -> list[PredictionEvaluationResult]:
        expired = self._prediction_store.list_expired()
        results: list[PredictionEvaluationResult] = []

        for record in expired:
            pred = Prediction(
                id=record["id"],
                target=record["target"],
                confidence=record["confidence"],
                source_pattern_id=record.get("source_pattern_id", ""),
                window_start=datetime.date.fromisoformat(record["window_start"]),
                window_end=datetime.date.fromisoformat(record["window_end"]),
                outcome=record.get("outcome"),
            )

            raw = self._observation_store.observations_in_range(
                pred.window_start, pred.window_end
            )
            observations = [
                Observation(
                    id=r.get("id", ""),
                    timestamp=datetime.datetime.fromisoformat(r.get("timestamp", "")),
                    type=r.get("type", "action"),
                    source_mechanism=r.get("source_mechanism", "auto"),
                    source_component=r.get("source_component", "unknown"),
                    summary=r.get("summary", ""),
                    project=r.get("project"),
                    energy=r.get("energy"),
                    tags=r.get("tags", []),
                )
                for r in raw
            ]
            outcome, conf_delta = self._evaluator.evaluate(pred, observations)
            self._prediction_store.update_outcome(pred.id, outcome)

            results.append(
                PredictionEvaluationResult(
                    prediction_id=pred.id,
                    outcome=outcome,
                    confidence_delta=conf_delta,
                )
            )

        return results
