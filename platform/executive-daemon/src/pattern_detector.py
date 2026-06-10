"""
pattern_detector.py — 7 pattern detection rules for the learning engine.

Each rule is a pure deterministic function that takes aggregated windows
(and optionally declared values or observation streams) and returns
a list of detected PatternCandidates (or None).

Rules:
  1. BehavioralBiasDetector     — consistent prioritization mismatch
  2. CyclicalPatternDetector    — recurring day-of-week activity patterns
  3. AttentionCliffDetector     — abrupt project attention drops
  4. DelegationPatternDetector  — systematic category deprioritization
  5. EnergyCorrelationDetector  — activity type ↔ energy level correlation
  6. CompletionSignatureDetector — conditions shared across completed projects
  7. RejectionPatternDetector   — operator consistently rejects pattern types
"""

import datetime
import statistics
from typing import NamedTuple

from learning_engine import (
    AggregatedWindow,
    ConfidenceScorer,
    FeedbackAction,
    Observation,
    PatternCandidate,
    PatternStatus,
    PatternType,
)


# ---------------------------------------------------------------------------
# Shared helpers for candidate construction
# ---------------------------------------------------------------------------

_scorer = ConfidenceScorer()


def _make_candidate(
    pattern_type: PatternType,
    title: str,
    description: str,
    windows: list[AggregatedWindow],
    suggestions: list[str],
    detection_count: int,
    pattern_counter: int,
    confidence: float | None = None,
    base_rate: float | None = None,
    consistency: float | None = None,
) -> PatternCandidate:
    if confidence is None:
        br = base_rate if base_rate is not None else min(1.0, len(windows) / 5.0)
        cs = consistency if consistency is not None else 0.0
        confidence = _scorer.score(br, cs, _scorer.compute_recency(0), 0.5, 0.0)
    return PatternCandidate(
        id=f"CND-{pattern_counter:04d}",
        pattern_type=pattern_type,
        confidence=confidence,
        title=title,
        description=description,
        evidence=windows[-3:],
        suggestions=suggestions,
        status=PatternStatus.CANDIDATE,
        requires_review=True,
        detection_count=detection_count,
    )


# ---------------------------------------------------------------------------
# 1. Behavioral Bias Detector
# ---------------------------------------------------------------------------


class ProjectPriorityPair(NamedTuple):
    project_a: str
    project_b: str
    weight_a: float
    weight_b: float


class BehavioralBiasDetector:
    def detect(
        self,
        windows: list[AggregatedWindow],
        pairs: list[ProjectPriorityPair],
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        if len(windows) < 3:
            return []
        candidates: list[PatternCandidate] = []
        for pair in pairs:
            consistent_bias_count = 0
            for w in windows:
                attention_a = w.by_project.get(pair.project_a, 0)
                attention_b = w.by_project.get(pair.project_b, 0)
                if attention_a == 0 and attention_b == 0:
                    continue
                ratio = attention_a / (attention_a + attention_b) if (attention_a + attention_b) > 0 else 0.5
                expected_ratio = pair.weight_a / (pair.weight_a + pair.weight_b) if (pair.weight_a + pair.weight_b) > 0 else 0.5
                if abs(ratio - expected_ratio) > 0.2:
                    consistent_bias_count += 1
            if consistent_bias_count >= len(windows) * 0.6:
                pattern_counter += 1
                candidates.append(
                    _make_candidate(
                        PatternType.BEHAVIORAL_BIAS,
                        f"Attention bias: {pair.project_a} vs {pair.project_b}",
                        f"{pair.project_a} (weight {pair.weight_a}) and {pair.project_b} "
                        f"(weight {pair.weight_b}) receive attention in a ratio that "
                        f"deviates from their declared weights in {consistent_bias_count}/{len(windows)} windows.",
                        windows,
                        [
                            f"Review declared weights for {pair.project_a} and {pair.project_b}",
                            f"Consider whether the attention split reflects actual priorities",
                        ],
                        consistent_bias_count,
                        pattern_counter,
                    )
                )
        return candidates


# ---------------------------------------------------------------------------
# 2. Cyclical Pattern Detector
# ---------------------------------------------------------------------------


class CyclicalPatternDetector:
    def detect(
        self,
        windows: list[AggregatedWindow],
        activity_domains: dict[str, str],  # tag -> domain label
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        if not windows:
            return []
        candidates: list[PatternCandidate] = []
        day_activity: dict[str, dict[str, int]] = {}
        for w in windows:
            if not w.by_day_of_week:
                continue
            for dow, _ in w.by_day_of_week.items():
                if dow not in day_activity:
                    day_activity[dow] = {}
        if not day_activity:
            return []
        dominant_days: dict[str, str] = {}
        for dow in day_activity:
            type_counts: dict[str, int] = {}
            for w in windows:
                if w.by_day_of_week and w.by_day_of_week.get(dow, 0) > 0:
                    for t, c in w.by_type.items():
                        if t in activity_domains:
                            type_counts[t] = type_counts.get(t, 0) + c
            if type_counts:
                dominant_type = max(type_counts, key=type_counts.get)
                total = sum(type_counts.values())
                share = type_counts[dominant_type] / total
                if share > 0.5 and total >= 3:
                    dominant_days[dow] = f"{activity_domains[dominant_type]} ({dominant_type})"
        if dominant_days:
            desc = "; ".join(f"{d}: {a}" for d, a in sorted(dominant_days.items()))
            pattern_counter += 1
            candidates.append(
                _make_candidate(
                    PatternType.CYCLICAL_PATTERN,
                    "Recurring weekly activity pattern detected",
                    f"Your week shows recurring patterns: {desc}",
                    windows,
                    [
                        "Review whether these patterns serve your stated priorities",
                        "Consider blocking recurring time for strategic vs reactive work",
                    ],
                    len(dominant_days),
                    pattern_counter,
                )
            )
        return candidates


# ---------------------------------------------------------------------------
# 3. Attention Cliff Detector
# ---------------------------------------------------------------------------


class AttentionCliffDetector:
    def __init__(self, drop_threshold: float = 0.8, min_windows: int = 3) -> None:
        self._drop_threshold = drop_threshold
        self._min_windows = min_windows

    def detect(
        self,
        windows: list[AggregatedWindow],
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        if len(windows) < self._min_windows:
            return []
        candidates: list[PatternCandidate] = []
        all_projects = set()
        for w in windows:
            all_projects.update(w.by_project.keys())
        for proj in all_projects:
            attention_series = [w.by_project.get(proj, 0) for w in windows]
            for i in range(1, len(attention_series)):
                prev = attention_series[i - 1]
                curr = attention_series[i]
                if prev > 0 and curr == 0:
                    drop_ratio = 1.0
                elif prev > 0:
                    drop_ratio = (prev - curr) / prev
                else:
                    continue
                if drop_ratio >= self._drop_threshold:
                    remaining = attention_series[i + 1:] if i + 1 < len(attention_series) else []
                    if not remaining or all(v == 0 for v in remaining):
                        pattern_counter += 1
                        candidates.append(
                            _make_candidate(
                                PatternType.ATTENTION_CLIFF,
                                f"Attention cliff: {proj}",
                                f"{proj} received attention in window {i} then dropped to near-zero "
                                f"in window {i + 1} and did not recover.",
                                windows[i - 1:i + 2] if i + 1 < len(windows) else windows[-3:],
                                [
                                    f"Review whether {proj} was completed or abandoned",
                                    "If abandoned, consider archiving or reprioritizing",
                                    f"Set a reminder to revisit {proj} in 30 days",
                                ],
                                1,
                                pattern_counter,
                            )
                        )
        return candidates


# ---------------------------------------------------------------------------
# 4. Delegation Pattern Detector
# ---------------------------------------------------------------------------


class CategoryAssignment(NamedTuple):
    project: str
    category: str


class DelegationPatternDetector:
    def detect(
        self,
        windows: list[AggregatedWindow],
        assignments: list[CategoryAssignment],
        category_weights: dict[str, float],  # category -> expected attention fraction
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        if len(windows) < 3:
            return []
        candidates: list[PatternCandidate] = []
        project_to_cat = {a.project: a.category for a in assignments}
        category_actual: dict[str, list[float]] = {}
        for w in windows:
            total = w.total_observations
            if total == 0:
                continue
            cat_totals: dict[str, int] = {}
            for proj, count in w.by_project.items():
                cat = project_to_cat.get(proj)
                if cat:
                    cat_totals[cat] = cat_totals.get(cat, 0) + count
            for cat, count in cat_totals.items():
                if cat not in category_actual:
                    category_actual[cat] = []
                category_actual[cat].append(count / total)
        for cat, expected in category_weights.items():
            actuals = category_actual.get(cat)
            if not actuals or len(actuals) < 3:
                continue
            mean_actual = statistics.mean(actuals)
            if expected > 0 and mean_actual < expected * 0.5:
                pattern_counter += 1
                candidates.append(
                    _make_candidate(
                        PatternType.DELEGATION_PATTERN,
                        f"Systematic deprioritization: {cat}",
                        f"Category '{cat}' has expected attention {expected:.0%} but "
                        f"receives {mean_actual:.0%} on average across {len(actuals)} windows.",
                        windows[-3:],
                        [
                            f"Review whether '{cat}' projects are correctly categorized",
                            f"Consider whether {cat} needs more explicit time blocking",
                            f"Evaluate whether {cat} weight should be reduced",
                        ],
                        int(sum(1 for a in actuals if a < expected * 0.5)),
                        pattern_counter,
                    )
                )
        return candidates


# ---------------------------------------------------------------------------
# 5. Energy Correlation Detector
# ---------------------------------------------------------------------------


class EnergyCorrelationResult(NamedTuple):
    activity_type: str
    dominant_energy: str
    share: float


class EnergyCorrelationDetector:
    def __init__(self, min_occurrences: int = 5) -> None:
        self._min_occurrences = min_occurrences

    def detect(
        self,
        windows: list[AggregatedWindow],
        observations: list[Observation],
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        if not windows or not observations:
            return []
        energy_by_type: dict[str, dict[str, int]] = {}
        for obs in observations:
            if not obs.energy:
                continue
            if obs.type not in energy_by_type:
                energy_by_type[obs.type] = {}
            energy_by_type[obs.type][obs.energy] = (
                energy_by_type[obs.type].get(obs.energy, 0) + 1
            )
        candidates: list[PatternCandidate] = []
        for activity_type, energy_counts in energy_by_type.items():
            total = sum(energy_counts.values())
            if total < self._min_occurrences:
                continue
            dominant_energy = max(energy_counts, key=energy_counts.get)
            share = energy_counts[dominant_energy] / total
            if share >= 0.6:
                pattern_counter += 1
                candidates.append(
                    _make_candidate(
                        PatternType.ENERGY_CORRELATION,
                        f"Energy correlation: {activity_type} ↔ {dominant_energy}",
                        f"'{activity_type}' activity occurs during '{dominant_energy}' energy "
                        f"periods {share:.0%} of the time ({total} occurrences).",
                        windows[-3:],
                        [
                            f"Schedule '{activity_type}' during your known {dominant_energy} periods",
                            f"Consider whether low-energy periods could be used for {activity_type}",
                        ],
                        total,
                        pattern_counter,
                    )
                )
        return candidates


# ---------------------------------------------------------------------------
# 6. Completion Signature Detector
# ---------------------------------------------------------------------------


class CompletionSignatureDetector:
    def detect(
        self,
        completed_projects: list[tuple[str, list[AggregatedWindow]]],
        abandoned_projects: list[tuple[str, list[AggregatedWindow]]],
        pattern_counter: int,
    ) -> list[PatternCandidate]:
        if not completed_projects or not abandoned_projects:
            return []
        completed_signatures: list[set[str]] = []
        for _, windows in completed_projects:
            sig = set()
            for w in windows:
                sig.update(w.by_type.keys())
            completed_signatures.append(sig)
        if not completed_signatures:
            return []
        common_conditions = completed_signatures[0].copy()
        for sig in completed_signatures[1:]:
            common_conditions &= sig
        abandoned_signatures: list[set[str]] = []
        for _, windows in abandoned_projects:
            sig = set()
            for w in windows:
                sig.update(w.by_type.keys())
            abandoned_signatures.append(sig)
        completion_unique = common_conditions.copy()
        for ab_sig in abandoned_signatures:
            completion_unique -= ab_sig
        if completion_unique:
            pattern_counter += 1
            return [
                _make_candidate(
                    PatternType.COMPLETION_SIGNATURE,
                    "Completion signature detected",
                    f"Projects that complete share activity types ({', '.join(sorted(completion_unique))}) "
                    f"that abandoned projects lack.",
                    [w for _, windows in completed_projects for w in windows][-3:],
                    [
                        "Ensure new projects include these activity types from the start",
                        "If a project lacks these types, consider whether it needs attention",
                    ],
                    len(completed_projects),
                    pattern_counter,
                )
            ]
        return []


# ---------------------------------------------------------------------------
# 7. Rejection Pattern Detector
# ---------------------------------------------------------------------------


class RejectionPatternDetector:
    def detect(
        self,
        feedback_history: dict[str, list[datetime.date]],
        pattern_counter: int,
        window_days: int = 60,
    ) -> list[PatternCandidate]:
        candidates: list[PatternCandidate] = []
        cutoff = datetime.date.today() - datetime.timedelta(days=window_days)
        for pattern_type, dates in feedback_history.items():
            recent = [d for d in dates if d >= cutoff]
            if len(recent) >= 3:
                rate = len(recent) / len(dates) if dates else 0
                pattern_counter += 1
                candidates.append(
                    _make_candidate(
                        PatternType.REJECTION_PATTERN,
                        f"Rejection pattern: '{pattern_type}' suggestions",
                        f"You have rejected {len(recent)} '{pattern_type}' suggestions in "
                        f"the last {window_days} days (rejection rate: {rate:.0%}).",
                        [],
                        [
                            f"Review whether '{pattern_type}' suggestions should be reduced",
                            f"Consider providing feedback on why these are being rejected",
                            "Adjust pattern detection thresholds for this pattern type",
                        ],
                        len(recent),
                        pattern_counter,
                    )
                )
        return candidates
