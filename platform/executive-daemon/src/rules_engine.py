"""
rules_engine.py — Layer 1 deterministic rules engine.

All rules in this engine are pure functions with no AI dependency.
They operate on attention-managed items and produce alerts, scores,
and priority rankings.

Rules:
  - Stall detection (wraps attention_manager.StallDetector)
  - Deadline scoring (wraps attention_manager.DeadlineScorer)
  - Fragmentation alerts (wraps attention_manager.FragmentationDetector)
  - Dependency traversal & unblocking notifications
  - Priority computation
"""

import datetime
from typing import NamedTuple

from attention_manager import (
    AttentionManager,
    AttentionState,
    DeadlineScorer,
    FragmentationDetector,
    StallDetector,
    TrackedItem,
)


class Commitment(NamedTuple):
    id: str
    deadline: datetime.date
    weight: float  # 0.0–1.0, operator-declared importance


class Dependency(NamedTuple):
    blocker_id: str  # Item that must be done first
    blocked_id: str  # Item that is blocked
    description: str


class PriorityResult(NamedTuple):
    item_id: str
    urgency: float       # 0.0–1.0 based on deadline score
    momentum: float      # 0.0–1.0 based on touch recency
    weight: float        # 0.0–1.0 priority weight from operator
    score: float         # urgency × weight × momentum


class UnblockingAlert(NamedTuple):
    unblocked_item_id: str
    blocker_item_id: str
    description: str


class RulesEngine:
    def __init__(self) -> None:
        self._attention_mgr = AttentionManager()
        self._stall_detector = StallDetector(stall_threshold_days=14)
        self._deadline_scorer = DeadlineScorer()
        self._frag_detector = FragmentationDetector(active_limit=5, dormant_limit=10)

    def compute_priorities(
        self,
        items: list[TrackedItem],
        commitments: list[Commitment],
        reference_date: datetime.date,
    ) -> list[PriorityResult]:
        deadline_map: dict[str, float] = {}
        for c in commitments:
            deadline_map[c.id] = self._deadline_scorer.score(
                (c.deadline - reference_date).days
            )
        results: list[PriorityResult] = []
        for item in items:
            urgency = 0.0
            weight = 0.3
            for c in commitments:
                if c.id == item.id:
                    urgency = deadline_map.get(c.id, 0.0)
                    weight = c.weight
                    break
            delta = (reference_date - item.last_touch).days
            momentum = max(0.0, 1.0 - (delta / 30.0)) if delta >= 0 else 1.0
            score = urgency * weight * momentum
            results.append(PriorityResult(item.id, urgency, momentum, weight, score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def check_stalls(
        self,
        items: list[TrackedItem],
        reference_date: datetime.date,
    ) -> list[TrackedItem]:
        return self._stall_detector.find_stalled(items, reference_date)

    def check_fragmentation(
        self,
        items: list[TrackedItem],
    ) -> dict[str, int]:
        return self._frag_detector.check(items)

    def check_unblocking(
        self,
        dependencies: list[Dependency],
        recently_touched_ids: set[str],
    ) -> list[UnblockingAlert]:
        alerts: list[UnblockingAlert] = []
        for dep in dependencies:
            if dep.blocker_id in recently_touched_ids:
                alerts.append(
                    UnblockingAlert(
                        unblocked_item_id=dep.blocked_id,
                        blocker_item_id=dep.blocker_id,
                        description=dep.description,
                    )
                )
        return alerts
