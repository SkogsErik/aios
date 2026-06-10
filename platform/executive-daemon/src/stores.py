"""
stores.py — File-based persistence for inferred patterns, contradictions,
predictions, and feedback history. Follows ADR-003 storage patterns.

Layout:
  platform/knowledge/patterns/
    YYYY/
      MM/
        YYYY-MM-DD.yaml      # Patterns created on this date
  platform/knowledge/contradictions/
    YYYY/
      MM/
        YYYY-MM-DD.yaml
  platform/knowledge/predictions/
    YYYY/
      MM/
        YYYY-MM-DD.yaml
"""

import datetime
import os
from pathlib import Path
from typing import NamedTuple

import yaml

from learning_engine import (
    AggregatedWindow,
    FeedbackAction,
    PatternCandidate,
    PatternStatus,
    PatternType,
    Prediction,
    Tension,
)


# ---------------------------------------------------------------------------
# Default storage paths
# ---------------------------------------------------------------------------

# Resolve base dir relative to repository root (3 levels up from src/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_BASE_DIR = _REPO_ROOT / "platform" / "knowledge"
PATTERNS_DIR = DEFAULT_BASE_DIR / "patterns"
CONTRADICTIONS_DIR = DEFAULT_BASE_DIR / "contradictions"
PREDICTIONS_DIR = DEFAULT_BASE_DIR / "predictions"
FEEDBACK_FILE = DEFAULT_BASE_DIR / "feedback_history.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dated_path(base: Path, d: datetime.date) -> Path:
    return base / str(d.year) / f"{d.month:02d}" / f"{d.isoformat()}.yaml"


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _make_serializable(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, PatternType):
        return obj.value
    if isinstance(obj, PatternStatus):
        return obj.value
    if isinstance(obj, FeedbackAction):
        return obj.value
    if isinstance(obj, AggregatedWindow):
        return {
            "window_start": obj.window_start.isoformat(),
            "window_end": obj.window_end.isoformat(),
            "total_observations": obj.total_observations,
            "by_type": obj.by_type,
            "by_project": obj.by_project,
            "by_energy": obj.by_energy,
            "deep_work_pct": obj.deep_work_pct,
            "by_source_component": obj.by_source_component,
            "by_day_of_week": obj.by_day_of_week,
        }
    return obj


# ---------------------------------------------------------------------------
# Pattern store
# ---------------------------------------------------------------------------


class PatternStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or PATTERNS_DIR

    def save(self, candidate: PatternCandidate) -> None:
        path = _dated_path(self._base, datetime.date.today())
        _ensure_dir(path)
        entry = {
            "id": candidate.id,
            "pattern_type": candidate.pattern_type.value,
            "confidence": candidate.confidence,
            "title": candidate.title,
            "description": candidate.description,
            "evidence": [_make_serializable(e) for e in candidate.evidence],
            "suggestions": candidate.suggestions,
            "status": candidate.status.value,
            "requires_review": candidate.requires_review,
            "detection_count": candidate.detection_count,
            "saved_at": datetime.datetime.now().isoformat(),
        }
        records: list[dict] = []
        if path.exists():
            with open(path) as f:
                records = yaml.safe_load(f) or []
        records.append(entry)
        with open(path, "w") as f:
            yaml.dump(records, f, default_flow_style=False, sort_keys=False)

    def list_recent(self, days: int = 90) -> list[dict]:
        cutoff = datetime.date.today() - datetime.timedelta(days=days)
        results: list[dict] = []
        for root, _dirs, files in os.walk(self._base):
            for fn in sorted(files, reverse=True):
                date_part = fn.replace(".yaml", "")
                try:
                    d = datetime.date.fromisoformat(date_part)
                except ValueError:
                    continue
                if d < cutoff:
                    continue
                with open(Path(root) / fn) as f:
                    records = yaml.safe_load(f) or []
                    results.extend(records)
        return results

    def delete_all(self) -> None:
        for root, _dirs, files in os.walk(self._base):
            for fn in files:
                os.remove(Path(root) / fn)


# ---------------------------------------------------------------------------
# Contradiction store
# ---------------------------------------------------------------------------


class ContradictionRecord(NamedTuple):
    attribute: str
    declared_value: float
    observed_value: float
    magnitude: float
    severity: str
    detected_at: datetime.date


class ContradictionStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or CONTRADICTIONS_DIR

    def save(self, tension: Tension) -> None:
        path = _dated_path(self._base, datetime.date.today())
        _ensure_dir(path)
        entry = {
            "attribute": tension.attribute,
            "declared_value": tension.declared_value,
            "observed_value": tension.observed_value,
            "magnitude": tension.magnitude,
            "severity": tension.severity,
            "detected_at": datetime.date.today().isoformat(),
        }
        records: list[dict] = []
        if path.exists():
            with open(path) as f:
                records = yaml.safe_load(f) or []
        records.append(entry)
        with open(path, "w") as f:
            yaml.dump(records, f, default_flow_style=False, sort_keys=False)

    def list_active(self, max_age_days: int = 90) -> list[dict]:
        cutoff = datetime.date.today() - datetime.timedelta(days=max_age_days)
        results: list[dict] = []
        for root, _dirs, files in os.walk(self._base):
            for fn in sorted(files, reverse=True):
                try:
                    d = datetime.date.fromisoformat(fn.replace(".yaml", ""))
                except ValueError:
                    continue
                if d < cutoff:
                    continue
                with open(Path(root) / fn) as f:
                    records = yaml.safe_load(f) or []
                    results.extend(records)
        return results

    def delete_all(self) -> None:
        for root, _dirs, files in os.walk(self._base):
            for fn in files:
                os.remove(Path(root) / fn)


# ---------------------------------------------------------------------------
# Prediction store
# ---------------------------------------------------------------------------


class PredictionStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or PREDICTIONS_DIR

    def save(self, prediction: Prediction) -> None:
        path = _dated_path(self._base, datetime.date.today())
        _ensure_dir(path)
        entry = {
            "id": prediction.id,
            "target": prediction.target,
            "confidence": prediction.confidence,
            "source_pattern_id": prediction.source_pattern_id,
            "window_start": prediction.window_start.isoformat(),
            "window_end": prediction.window_end.isoformat(),
            "outcome": prediction.outcome,
            "saved_at": datetime.datetime.now().isoformat(),
        }
        records: list[dict] = []
        if path.exists():
            with open(path) as f:
                records = yaml.safe_load(f) or []
        records.append(entry)
        with open(path, "w") as f:
            yaml.dump(records, f, default_flow_style=False, sort_keys=False)

    def list_pending(self) -> list[dict]:
        results: list[dict] = []
        for root, _dirs, files in os.walk(self._base):
            for fn in sorted(files, reverse=True):
                with open(Path(root) / fn) as f:
                    records = yaml.safe_load(f) or []
                    for r in records:
                        if r.get("outcome") is None:
                            results.append(r)
        return results

    def list_expired(self) -> list[dict]:
        today = datetime.date.today()
        results: list[dict] = []
        for root, _dirs, files in os.walk(self._base):
            for fn in sorted(files, reverse=True):
                with open(Path(root) / fn) as f:
                    records = yaml.safe_load(f) or []
                    for r in records:
                        end = datetime.date.fromisoformat(r["window_end"])
                        if r.get("outcome") is None and end < today:
                            results.append(r)
        return results

    def update_outcome(self, prediction_id: str, outcome: str) -> bool:
        for root, _dirs, files in os.walk(self._base):
            for fn in files:
                path = Path(root) / fn
                with open(path) as f:
                    records = yaml.safe_load(f) or []
                updated = False
                for r in records:
                    if r.get("id") == prediction_id:
                        r["outcome"] = outcome
                        r["evaluated_at"] = datetime.datetime.now().isoformat()
                        updated = True
                if updated:
                    with open(path, "w") as f:
                        yaml.dump(records, f, default_flow_style=False, sort_keys=False)
                    return True
        return False

    def delete_all(self) -> None:
        for root, _dirs, files in os.walk(self._base):
            for fn in files:
                os.remove(Path(root) / fn)


# ---------------------------------------------------------------------------
# Feedback history store
# ---------------------------------------------------------------------------


class FeedbackHistoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or FEEDBACK_FILE

    def load(self) -> dict[str, list[str]]:
        if not self._path.exists():
            return {}
        with open(self._path) as f:
            return yaml.safe_load(f) or {}

    def save(self, history: dict[str, list[str]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            yaml.dump(history, f, default_flow_style=False, sort_keys=False)
