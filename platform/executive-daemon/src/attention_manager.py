"""
attention_manager.py — Track attention state for projects, goals, and commitments.

Attention states:
  - active:     Currently being worked on or recently touched
  - dormant:    Not touched recently but still relevant
  - forgotten:  Not touched for a long time, flagged for review
  - resurfaced: Recently moved from forgotten back to active or dormant

Decay moves items from active → dormant → forgotten over time without
touches. Touch events (observation, workflow run, manual note) reset
the decay clock for the associated item.
"""

import datetime
import enum
from typing import NamedTuple


ATTENTION_DECAY_DAYS: dict[str, int] = {
    "active_to_dormant": 7,
    "dormant_to_forgotten": 21,
}


class AttentionState(enum.Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    FORGOTTEN = "forgotten"
    RESURFACED = "resurfaced"

    def __str__(self) -> str:
        return self.value


class TrackedItem(NamedTuple):
    id: str
    attention_state: AttentionState
    last_touch: datetime.date
    kind: str  # "project" | "goal" | "commitment"


class AttentionManager:
    def __init__(self, decay_days: dict[str, int] | None = None) -> None:
        if decay_days is None:
            decay_days = ATTENTION_DECAY_DAYS
        self._active_to_dormant = decay_days["active_to_dormant"]
        self._dormant_to_forgotten = decay_days["dormant_to_forgotten"]

    def compute_next_state(
        self, item: TrackedItem, reference_date: datetime.date
    ) -> AttentionState:
        delta = (reference_date - item.last_touch).days
        if item.attention_state == AttentionState.ACTIVE:
            if delta >= self._active_to_dormant:
                return AttentionState.DORMANT
            return AttentionState.ACTIVE
        if item.attention_state == AttentionState.DORMANT:
            if delta >= self._dormant_to_forgotten:
                return AttentionState.FORGOTTEN
            return AttentionState.DORMANT
        if item.attention_state == AttentionState.RESURFACED:
            return AttentionState.ACTIVE
        return item.attention_state

    def touch_item(self, item: TrackedItem, reference_date: datetime.date) -> TrackedItem:
        new_state = (
            AttentionState.RESURFACED
            if item.attention_state in (AttentionState.FORGOTTEN, AttentionState.DORMANT)
            else item.attention_state
        )
        return TrackedItem(item.id, new_state, reference_date, item.kind)

    def evaluate_all(
        self, items: list[TrackedItem], reference_date: datetime.date
    ) -> list[tuple[TrackedItem, AttentionState]]:
        results: list[tuple[TrackedItem, AttentionState]] = []
        for item in items:
            new_state = self.compute_next_state(item, reference_date)
            if new_state != item.attention_state:
                results.append((item, new_state))
        return results


class StallDetector:
    def __init__(self, stall_threshold_days: int = 14) -> None:
        self._threshold = stall_threshold_days

    def find_stalled(
        self, items: list[TrackedItem], reference_date: datetime.date
    ) -> list[TrackedItem]:
        stalled: list[TrackedItem] = []
        for item in items:
            if item.attention_state in (AttentionState.ACTIVE, AttentionState.DORMANT):
                delta = (reference_date - item.last_touch).days
                if delta >= self._threshold:
                    stalled.append(item)
        return stalled


class DeadlineScorer:
    def score(self, days_until_deadline: int) -> float:
        if days_until_deadline <= 0:
            return 1.0
        return max(0.0, 1.0 - (days_until_deadline / 90.0))


class FragmentationDetector:
    def __init__(self, active_limit: int = 5, dormant_limit: int = 10) -> None:
        self._active_limit = active_limit
        self._dormant_limit = dormant_limit

    def check(
        self, items: list[TrackedItem]
    ) -> dict[str, int]:
        active_count = sum(
            1 for i in items if i.attention_state == AttentionState.ACTIVE
        )
        dormant_count = sum(
            1 for i in items if i.attention_state == AttentionState.DORMANT
        )
        alerts: dict[str, int] = {}
        if active_count > self._active_limit:
            alerts["active_over_limit"] = active_count
        if dormant_count > self._dormant_limit:
            alerts["dormant_over_limit"] = dormant_count
        return alerts
