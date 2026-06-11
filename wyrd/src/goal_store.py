"""
goal_store.py — File-based stores for goals and focus areas.

Follows ADR-003 storage patterns (file-based YAML, inspectable, version-controlled).
Paths are resolved relative to the repository root to work regardless of CWD.

Stores:
  GoalStore        — platform/knowledge/goals/GL-NNN.yaml
  FocusAreaStore   — platform/knowledge/focus-areas/FCA-NNN.yaml

Subsystem: Wyrd (ADR-012)
Capability: CAP-011 (Identity and Persona Management)
Defined by: ADR-007 — Identity as Domain Object
"""

import datetime
import re
import shutil
from pathlib import Path
from typing import NamedTuple, Optional

import yaml

# ---------------------------------------------------------------------------
# Path resolution — wyrd/src/ is 3 levels from repo root (src→wyrd→aios)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_KNOWLEDGE_DIR = _REPO_ROOT / "platform" / "knowledge"

_GOALS_DIR = _KNOWLEDGE_DIR / "goals"
_FOCUS_AREAS_DIR = _KNOWLEDGE_DIR / "focus-areas"

_GL_PATTERN = re.compile(r"^GL-(\d+)$")
_FCA_PATTERN = re.compile(r"^FCA-(\d+)$")


def _parse_date(value) -> Optional[datetime.date]:
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


# ---------------------------------------------------------------------------
# Goal data type
# ---------------------------------------------------------------------------


class Goal(NamedTuple):
    id: str
    title: str
    type: str                               # outcome | aspiration | learning | habit
    status: str                             # draft | active | paused | achieved | abandoned
    created: datetime.date
    updated: datetime.date
    description: Optional[str] = None
    horizon: Optional[str] = None           # 1-week | 1-month | 3-month | 6-month | 1-year | multi-year | ongoing
    focus_area: Optional[str] = None        # FCA-NNN
    outcome_statement: Optional[str] = None
    why: Optional[str] = None
    target_date: Optional[datetime.date] = None
    priority_weight: float = 0.5
    projects: list = []                     # PRJ-NNN IDs
    tags: list = []


# ---------------------------------------------------------------------------
# GoalStore
# ---------------------------------------------------------------------------


class GoalStore:
    """
    File-based store for Goal entities.

    One YAML file per goal: platform/knowledge/goals/GL-NNN.yaml
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._dir = (base_dir or _GOALS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, goal_id: str) -> Path:
        return self._dir / f"{goal_id}.yaml"

    # ------------------------------------------------------------------
    # ID allocation
    # ------------------------------------------------------------------

    def next_id(self) -> str:
        """Return the next available GL-NNN identifier."""
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob("GL-*.yaml"):
                m = _GL_PATTERN.match(f.stem)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        return f"GL-{max_n + 1:03d}"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, goal: Goal) -> None:
        """Persist a goal to its YAML file (atomic write)."""
        self._ensure_dir()
        data = {
            "id": goal.id,
            "title": goal.title,
            "type": goal.type,
            "status": goal.status,
            "created": goal.created.isoformat(),
            "updated": datetime.date.today().isoformat(),
            "description": goal.description,
            "horizon": goal.horizon,
            "focus_area": goal.focus_area,
            "outcome_statement": goal.outcome_statement,
            "why": goal.why,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "priority_weight": goal.priority_weight,
            "projects": goal.projects or [],
            "tags": goal.tags or [],
        }
        path = self._path_for(goal.id)
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def update_status(self, goal_id: str, status: str) -> Optional[Goal]:
        """Update the lifecycle status of a goal."""
        goal = self.get(goal_id)
        if goal is None:
            return None
        updated = goal._replace(status=status)
        self.save(updated)
        return updated

    def link_project(self, goal_id: str, project_id: str) -> Optional[Goal]:
        """Associate a project with this goal (idempotent)."""
        goal = self.get(goal_id)
        if goal is None:
            return None
        projects = list(goal.projects or [])
        if project_id not in projects:
            projects.append(project_id)
        updated = goal._replace(projects=projects)
        self.save(updated)
        return updated

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def _from_dict(self, data: dict) -> Goal:
        return Goal(
            id=data["id"],
            title=data["title"],
            type=data.get("type", "outcome"),
            status=data.get("status", "draft"),
            created=_parse_date(data.get("created")),
            updated=_parse_date(data.get("updated")),
            description=data.get("description"),
            horizon=data.get("horizon"),
            focus_area=data.get("focus_area"),
            outcome_statement=data.get("outcome_statement"),
            why=data.get("why"),
            target_date=_parse_date(data.get("target_date")),
            priority_weight=float(data.get("priority_weight", 0.5)),
            projects=data.get("projects") or [],
            tags=data.get("tags") or [],
        )

    def get(self, goal_id: str) -> Optional[Goal]:
        """Return a goal by ID, or None if not found."""
        path = self._path_for(goal_id)
        if not path.exists():
            return None
        with open(path) as f:
            return self._from_dict(yaml.safe_load(f))

    def list_all(self) -> list:
        """Return all goals sorted by ID."""
        if not self._dir.exists():
            return []
        goals = []
        for path in sorted(self._dir.glob("GL-*.yaml")):
            with open(path) as f:
                goals.append(self._from_dict(yaml.safe_load(f)))
        return goals

    def list_active(self) -> list:
        """Return goals with status == 'active'."""
        return [g for g in self.list_all() if g.status == "active"]

    def init(
        self,
        title: str,
        type: str = "outcome",
        horizon: Optional[str] = None,
        focus_area: Optional[str] = None,
        description: Optional[str] = None,
        why: Optional[str] = None,
        outcome_statement: Optional[str] = None,
        target_date: Optional[datetime.date] = None,
        priority_weight: float = 0.5,
        tags: list = [],
    ) -> Goal:
        """Create and persist a new goal, returning the saved entity."""
        today = datetime.date.today()
        goal_id = self.next_id()
        goal = Goal(
            id=goal_id,
            title=title,
            type=type,
            status="draft",
            created=today,
            updated=today,
            description=description,
            horizon=horizon,
            focus_area=focus_area,
            outcome_statement=outcome_statement,
            why=why,
            target_date=target_date,
            priority_weight=priority_weight,
            tags=list(tags),
        )
        self.save(goal)
        return self.get(goal_id)


# ---------------------------------------------------------------------------
# FocusArea data type
# ---------------------------------------------------------------------------


class FocusArea(NamedTuple):
    id: str
    title: str
    status: str                             # active | paused | archived
    created: datetime.date
    updated: datetime.date
    description: Optional[str] = None
    why_it_matters: Optional[str] = None
    attention_budget: Optional[str] = None  # primary | secondary | maintenance | minimal
    goals: list = []                        # GL-NNN IDs
    tags: list = []


# ---------------------------------------------------------------------------
# FocusAreaStore
# ---------------------------------------------------------------------------


class FocusAreaStore:
    """
    File-based store for FocusArea entities.

    One YAML file per focus area: platform/knowledge/focus-areas/FCA-NNN.yaml
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._dir = (base_dir or _FOCUS_AREAS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, area_id: str) -> Path:
        return self._dir / f"{area_id}.yaml"

    # ------------------------------------------------------------------
    # ID allocation
    # ------------------------------------------------------------------

    def next_id(self) -> str:
        """Return the next available FCA-NNN identifier."""
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob("FCA-*.yaml"):
                m = _FCA_PATTERN.match(f.stem)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        return f"FCA-{max_n + 1:03d}"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, area: FocusArea) -> None:
        """Persist a focus area to its YAML file (atomic write)."""
        self._ensure_dir()
        data = {
            "id": area.id,
            "title": area.title,
            "status": area.status,
            "created": area.created.isoformat(),
            "updated": datetime.date.today().isoformat(),
            "description": area.description,
            "why_it_matters": area.why_it_matters,
            "attention_budget": area.attention_budget,
            "goals": area.goals or [],
            "tags": area.tags or [],
        }
        path = self._path_for(area.id)
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def update_status(self, area_id: str, status: str) -> Optional[FocusArea]:
        """Update the lifecycle status of a focus area."""
        area = self.get(area_id)
        if area is None:
            return None
        updated = area._replace(status=status)
        self.save(updated)
        return updated

    def link_goal(self, area_id: str, goal_id: str) -> Optional[FocusArea]:
        """Associate a goal with this focus area (idempotent)."""
        area = self.get(area_id)
        if area is None:
            return None
        goals = list(area.goals or [])
        if goal_id not in goals:
            goals.append(goal_id)
        updated = area._replace(goals=goals)
        self.save(updated)
        return updated

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def _from_dict(self, data: dict) -> FocusArea:
        return FocusArea(
            id=data["id"],
            title=data["title"],
            status=data.get("status", "active"),
            created=_parse_date(data.get("created")),
            updated=_parse_date(data.get("updated")),
            description=data.get("description"),
            why_it_matters=data.get("why_it_matters"),
            attention_budget=data.get("attention_budget"),
            goals=data.get("goals") or [],
            tags=data.get("tags") or [],
        )

    def get(self, area_id: str) -> Optional[FocusArea]:
        """Return a focus area by ID, or None if not found."""
        path = self._path_for(area_id)
        if not path.exists():
            return None
        with open(path) as f:
            return self._from_dict(yaml.safe_load(f))

    def list_all(self) -> list:
        """Return all focus areas sorted by ID."""
        if not self._dir.exists():
            return []
        areas = []
        for path in sorted(self._dir.glob("FCA-*.yaml")):
            with open(path) as f:
                areas.append(self._from_dict(yaml.safe_load(f)))
        return areas

    def list_active(self) -> list:
        """Return focus areas with status == 'active'."""
        return [a for a in self.list_all() if a.status == "active"]

    def init(
        self,
        title: str,
        description: Optional[str] = None,
        why_it_matters: Optional[str] = None,
        attention_budget: Optional[str] = None,
        tags: list = [],
    ) -> FocusArea:
        """Create and persist a new focus area, returning the saved entity."""
        today = datetime.date.today()
        area_id = self.next_id()
        area = FocusArea(
            id=area_id,
            title=title,
            status="active",
            created=today,
            updated=today,
            description=description,
            why_it_matters=why_it_matters,
            attention_budget=attention_budget,
            tags=list(tags),
        )
        self.save(area)
        return self.get(area_id)
