"""
project_store.py — File-based stores for projects, commitments, and persona.

Follows ADR-003 storage patterns (file-based YAML, inspectable, version-controlled).
Paths are resolved relative to the repository root to work regardless of CWD.

Stores:
  ProjectStore     — platform/knowledge/projects/PRJ-NNN.yaml
  CommitmentStore  — platform/knowledge/commitments/CMT-NNN.yaml
  PersonaStore     — platform/knowledge/persona/persona.yaml

Capability: CAP-011 (Identity and Persona Management), CAP-013 (Executive Function)
Defined by: ADR-007 — Identity as Domain Object
"""

import datetime
import re
import shutil
from pathlib import Path
from typing import NamedTuple, Optional

import yaml

from attention_manager import AttentionState, TrackedItem
from rules_engine import Commitment

# ---------------------------------------------------------------------------
# Path resolution (absolute, relative to repo root)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_KNOWLEDGE_DIR = _REPO_ROOT / "platform" / "knowledge"

_PROJECTS_DIR = _KNOWLEDGE_DIR / "projects"
_COMMITMENTS_DIR = _KNOWLEDGE_DIR / "commitments"
_PERSONA_DIR = _KNOWLEDGE_DIR / "persona"

_PRJ_PATTERN = re.compile(r"^PRJ-(\d+)$")
_CMT_PATTERN = re.compile(r"^CMT-(\d+)$")


# ---------------------------------------------------------------------------
# Project data type
# ---------------------------------------------------------------------------


class Project(NamedTuple):
    id: str
    title: str
    type: str                           # project | initiative | maintenance
    status: str                         # draft | active | paused | at_risk | stalled | completed | cancelled | abandoned
    created: datetime.date
    updated: datetime.date
    goal: Optional[str] = None          # GL-NNN
    focus_area: Optional[str] = None    # FCA-NNN
    description: Optional[str] = None
    outcome_statement: Optional[str] = None
    target_completion: Optional[datetime.date] = None
    attention_state: str = "active"     # active | dormant | forgotten | resurfaced
    last_touch: Optional[datetime.date] = None
    health: str = "on_track"            # on_track | at_risk | blocked | stalled
    priority_weight: float = 0.5        # 0.0–1.0
    tags: list = []
    commitments: list = []              # CMT-NNN IDs


# ---------------------------------------------------------------------------
# ProjectStore
# ---------------------------------------------------------------------------


class ProjectStore:
    """
    File-based store for Project entities.

    One YAML file per project: platform/knowledge/projects/PRJ-NNN.yaml
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._dir = (base_dir or _PROJECTS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, project_id: str) -> Path:
        return self._dir / f"{project_id}.yaml"

    # ------------------------------------------------------------------
    # ID allocation
    # ------------------------------------------------------------------

    def next_id(self) -> str:
        """Return the next available PRJ-NNN identifier."""
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob("PRJ-*.yaml"):
                m = _PRJ_PATTERN.match(f.stem)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        return f"PRJ-{max_n + 1:03d}"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, project: Project) -> None:
        """Persist a project to its YAML file (atomic write)."""
        self._ensure_dir()
        data = {
            "id": project.id,
            "title": project.title,
            "type": project.type,
            "status": project.status,
            "created": project.created.isoformat(),
            "updated": datetime.date.today().isoformat(),
            "goal": project.goal,
            "focus_area": project.focus_area,
            "description": project.description,
            "outcome_statement": project.outcome_statement,
            "target_completion": project.target_completion.isoformat() if project.target_completion else None,
            "attention": {
                "state": project.attention_state,
                "last_touch": (project.last_touch or datetime.date.today()).isoformat(),
            },
            "health": project.health,
            "priority_weight": project.priority_weight,
            "tags": project.tags or [],
            "commitments": project.commitments or [],
        }
        path = self._path_for(project.id)
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def touch(self, project_id: str, when: Optional[datetime.date] = None) -> Optional[Project]:
        """Record attention on a project (resets decay clock). Returns updated project."""
        project = self.get(project_id)
        if project is None:
            return None
        touch_date = when or datetime.date.today()
        # Resurface if coming from dormant/forgotten
        new_attention = project.attention_state
        if project.attention_state in ("dormant", "forgotten"):
            new_attention = "resurfaced"
        updated = project._replace(
            last_touch=touch_date,
            attention_state=new_attention,
        )
        self.save(updated)
        return updated

    def update_status(self, project_id: str, status: str) -> Optional[Project]:
        """Update the lifecycle status of a project."""
        project = self.get(project_id)
        if project is None:
            return None
        updated = project._replace(status=status)
        self.save(updated)
        return updated

    def update_attention_state(self, project_id: str, state: str) -> Optional[Project]:
        """Update the attention state of a project (used by daemon decay loop)."""
        project = self.get(project_id)
        if project is None:
            return None
        updated = project._replace(attention_state=state)
        self.save(updated)
        return updated

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, project_id: str) -> Optional[Project]:
        """Return a project by ID, or None if not found."""
        path = self._path_for(project_id)
        if not path.exists():
            return None
        return self._load(path)

    def list_all(self) -> list[Project]:
        """Return all projects."""
        if not self._dir.exists():
            return []
        projects = []
        for path in sorted(self._dir.glob("PRJ-*.yaml")):
            try:
                projects.append(self._load(path))
            except Exception:
                continue
        return projects

    def list_active(self) -> list[Project]:
        """Return projects with status=active or status=at_risk."""
        return [p for p in self.list_all() if p.status in ("active", "at_risk", "stalled")]

    # ------------------------------------------------------------------
    # Rules engine integration
    # ------------------------------------------------------------------

    def list_as_tracked_items(self) -> list[TrackedItem]:
        """
        Return all non-terminal projects as TrackedItems for the rules engine.
        Terminal statuses (completed, cancelled, abandoned) are excluded.
        """
        terminal = {"completed", "cancelled", "abandoned"}
        today = datetime.date.today()
        items: list[TrackedItem] = []
        for project in self.list_all():
            if project.status in terminal:
                continue
            try:
                state = AttentionState(project.attention_state)
            except ValueError:
                state = AttentionState.ACTIVE
            last_touch = project.last_touch or project.created
            items.append(TrackedItem(
                id=project.id,
                attention_state=state,
                last_touch=last_touch,
                kind="project",
            ))
        return items

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self, path: Path) -> Project:
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        created = _parse_date(data.get("created")) or datetime.date.today()
        updated = _parse_date(data.get("updated")) or datetime.date.today()
        attention = data.get("attention", {})
        last_touch = _parse_date(attention.get("last_touch")) or created

        return Project(
            id=data["id"],
            title=data.get("title", ""),
            type=data.get("type", "project"),
            status=data.get("status", "draft"),
            created=created,
            updated=updated,
            goal=data.get("goal"),
            focus_area=data.get("focus_area"),
            description=data.get("description"),
            outcome_statement=data.get("outcome_statement"),
            target_completion=_parse_date(data.get("target_completion")),
            attention_state=attention.get("state", "active"),
            last_touch=last_touch,
            health=data.get("health", "on_track"),
            priority_weight=float(data.get("priority_weight", 0.5)),
            tags=data.get("tags") or [],
            commitments=data.get("commitments") or [],
        )


# ---------------------------------------------------------------------------
# CommitmentData type (separate from rules_engine.Commitment for persistence)
# ---------------------------------------------------------------------------


class CommitmentData(NamedTuple):
    id: str
    description: str
    deadline: datetime.date
    status: str                         # active | fulfilled | broken | deferred | cancelled
    created: datetime.date
    updated: datetime.date
    project: Optional[str] = None       # PRJ-NNN
    promisee: str = "self"
    weight: float = 0.5                 # 0.0–1.0 for priority scoring
    consequences: Optional[str] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# CommitmentStore
# ---------------------------------------------------------------------------


class CommitmentStore:
    """
    File-based store for Commitment entities.

    One YAML file per commitment: platform/knowledge/commitments/CMT-NNN.yaml
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._dir = (base_dir or _COMMITMENTS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, commitment_id: str) -> Path:
        return self._dir / f"{commitment_id}.yaml"

    def next_id(self) -> str:
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob("CMT-*.yaml"):
                m = _CMT_PATTERN.match(f.stem)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        return f"CMT-{max_n + 1:03d}"

    def save(self, commitment: CommitmentData) -> None:
        self._ensure_dir()
        data = {
            "id": commitment.id,
            "description": commitment.description,
            "deadline": commitment.deadline.isoformat(),
            "status": commitment.status,
            "created": commitment.created.isoformat(),
            "updated": datetime.date.today().isoformat(),
            "project": commitment.project,
            "promisee": commitment.promisee,
            "weight": commitment.weight,
            "consequences": commitment.consequences,
            "notes": commitment.notes,
        }
        path = self._path_for(commitment.id)
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def get(self, commitment_id: str) -> Optional[CommitmentData]:
        path = self._path_for(commitment_id)
        if not path.exists():
            return None
        return self._load(path)

    def list_all(self) -> list[CommitmentData]:
        if not self._dir.exists():
            return []
        commitments = []
        for path in sorted(self._dir.glob("CMT-*.yaml")):
            try:
                commitments.append(self._load(path))
            except Exception:
                continue
        return commitments

    def list_active(self) -> list[CommitmentData]:
        return [c for c in self.list_all() if c.status == "active"]

    def list_as_rules_engine_commitments(self) -> list[Commitment]:
        """Return active commitments as rules_engine.Commitment NamedTuples."""
        return [
            Commitment(id=c.id, deadline=c.deadline, weight=c.weight)
            for c in self.list_active()
        ]

    def _load(self, path: Path) -> CommitmentData:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return CommitmentData(
            id=data["id"],
            description=data.get("description", ""),
            deadline=_parse_date(data["deadline"]) or datetime.date.today(),
            status=data.get("status", "active"),
            created=_parse_date(data.get("created")) or datetime.date.today(),
            updated=_parse_date(data.get("updated")) or datetime.date.today(),
            project=data.get("project"),
            promisee=data.get("promisee", "self"),
            weight=float(data.get("weight", 0.5)),
            consequences=data.get("consequences"),
            notes=data.get("notes"),
        )


# ---------------------------------------------------------------------------
# Persona data type
# ---------------------------------------------------------------------------


class DeclaredFact(NamedTuple):
    statement: str
    category: str       # value | belief | preference | habit | constraint
    confidence: str     # high | medium | low
    declared_at: datetime.date


class PersonaValue(NamedTuple):
    value: str
    priority: int
    category: str       # personal | professional | intellectual


class PersonaPreference(NamedTuple):
    domain: str
    preference: str
    context: str
    source: str         # declared | inferred
    confidence: float


class Persona(NamedTuple):
    id: str
    version: int
    created: datetime.date
    updated: datetime.date
    name: Optional[str] = None
    declared_facts: list = []
    values: list = []
    preferences: list = []
    inferred_attributes: list = []


# ---------------------------------------------------------------------------
# PersonaStore
# ---------------------------------------------------------------------------


class PersonaStore:
    """
    File-based store for the operator Persona (single file: persona.yaml).

    Canonical attributes (declared_facts, values, preferences) are
    operator-authored. Inferred attributes are derived output from the
    learning engine and must be reviewed before promotion.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._dir = (base_dir or _PERSONA_DIR).resolve()
        self._path = self._dir / "persona.yaml"

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        return self._path.exists()

    def load(self) -> Optional[Persona]:
        if not self._path.exists():
            return None
        with open(self._path) as f:
            data = yaml.safe_load(f) or {}
        return Persona(
            id=data.get("id", "PRS-001"),
            version=int(data.get("version", 1)),
            created=_parse_date(data.get("created")) or datetime.date.today(),
            updated=_parse_date(data.get("updated")) or datetime.date.today(),
            name=data.get("name"),
            declared_facts=data.get("declared_facts") or [],
            values=data.get("values") or [],
            preferences=data.get("preferences") or [],
            inferred_attributes=data.get("inferred_attributes") or [],
        )

    def save(self, persona: Persona) -> None:
        self._ensure_dir()
        data = {
            "id": persona.id,
            "version": persona.version + 1,
            "created": persona.created.isoformat(),
            "updated": datetime.date.today().isoformat(),
            "name": persona.name,
            "declared_facts": [
                {
                    "statement": f.statement,
                    "category": f.category,
                    "confidence": f.confidence,
                    "declared_at": f.declared_at.isoformat(),
                }
                for f in (persona.declared_facts or [])
                if isinstance(f, DeclaredFact)
            ] or persona.declared_facts or [],
            "values": [
                {"value": v.value, "priority": v.priority, "category": v.category}
                for v in (persona.values or [])
                if isinstance(v, PersonaValue)
            ] or persona.values or [],
            "preferences": [
                {
                    "domain": p.domain,
                    "preference": p.preference,
                    "context": p.context,
                    "source": p.source,
                    "confidence": p.confidence,
                }
                for p in (persona.preferences or [])
                if isinstance(p, PersonaPreference)
            ] or persona.preferences or [],
            "inferred_attributes": persona.inferred_attributes or [],
        }
        tmp = self._path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(self._path))

    def init(self, name: Optional[str] = None) -> Persona:
        """Create a new empty persona if one does not exist."""
        if self.exists():
            raise FileExistsError(f"Persona already exists at {self._path}")
        persona = Persona(
            id="PRS-001",
            version=1,
            created=datetime.date.today(),
            updated=datetime.date.today(),
            name=name,
        )
        self.save(persona)
        return persona

    def add_value(self, value: str, priority: int, category: str = "professional") -> Persona:
        persona = self.load()
        if persona is None:
            persona = self.init()
        existing = [v for v in (persona.values or []) if isinstance(v, dict)]
        existing.append({"value": value, "priority": priority, "category": category})
        updated = persona._replace(values=existing)
        self.save(updated)
        return updated

    def add_fact(self, statement: str, category: str = "belief", confidence: str = "medium") -> Persona:
        persona = self.load()
        if persona is None:
            persona = self.init()
        existing = list(persona.declared_facts or [])
        existing.append({
            "statement": statement,
            "category": category,
            "confidence": confidence,
            "declared_at": datetime.date.today().isoformat(),
        })
        updated = persona._replace(declared_facts=existing)
        self.save(updated)
        return updated


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _parse_date(val) -> Optional[datetime.date]:
    """Safely parse a date from a YAML value (string or date object)."""
    if val is None:
        return None
    if isinstance(val, datetime.date):
        return val
    try:
        return datetime.date.fromisoformat(str(val)[:10])
    except (ValueError, TypeError):
        return None
