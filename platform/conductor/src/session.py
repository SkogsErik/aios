"""
session.py — Conductor session model and persistence.

A session is a named conversation between the operator and the Conductor.
Sessions are stored as YAML files following ADR-003 (file-based, human-readable).

Storage: platform/knowledge/sessions/SES-YYYY-MMDD-NNN.yaml

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import datetime
import re
import shutil
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Path resolution — platform/conductor/src/ is 4 parents from repo root
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SESSIONS_DIR = _REPO_ROOT / "platform" / "knowledge" / "sessions"

_SES_PATTERN = re.compile(r"^SES-(\d{4}-\d{4})-(\d+)$")


# ---------------------------------------------------------------------------
# Data types (plain dicts for flexibility in YAML round-trip)
# ---------------------------------------------------------------------------


def make_turn(role: str, content: str, tool: Optional[str] = None) -> dict:
    """Create a conversation turn dict."""
    return {
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
    }


def make_session(
    session_id: str,
    title: Optional[str] = None,
    context_snapshot: Optional[dict] = None,
) -> dict:
    """Create a new session dict."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "id": session_id,
        "title": title,
        "status": "active",
        "created": now,
        "updated": now,
        "turns": [],
        "context_snapshot": context_snapshot or {},
    }


# ---------------------------------------------------------------------------
# SessionStore
# ---------------------------------------------------------------------------


class SessionStore:
    """
    File-based store for Conductor sessions.

    One YAML file per session: platform/knowledge/sessions/SES-YYYY-MMDD-NNN.yaml
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self._dir = (base_dir or _SESSIONS_DIR).resolve()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.yaml"

    # ------------------------------------------------------------------
    # ID allocation
    # ------------------------------------------------------------------

    def next_id(self, when: Optional[datetime.date] = None) -> str:
        """Return the next SES-YYYY-MMDD-NNN identifier for the given date."""
        date = when or datetime.date.today()
        prefix = date.strftime("%Y-%m%d")
        max_n = 0
        if self._dir.exists():
            for f in self._dir.glob(f"SES-{prefix}-*.yaml"):
                m = _SES_PATTERN.match(f.stem)
                if m and m.group(1) == prefix:
                    max_n = max(max_n, int(m.group(2)))
        return f"SES-{prefix}-{max_n + 1:03d}"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, session: dict) -> None:
        """Persist a session dict to YAML (atomic write)."""
        self._ensure_dir()
        data = dict(session)
        data["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        path = self._path_for(session["id"])
        tmp = path.with_suffix(".yaml.tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        shutil.move(str(tmp), str(path))

    def add_turn(self, session_id: str, turn: dict) -> Optional[dict]:
        """Append a turn to a session and re-persist. Returns updated session."""
        session = self.get(session_id)
        if session is None:
            return None
        session["turns"] = list(session.get("turns") or []) + [turn]
        self.save(session)
        return self.get(session_id)

    def archive(self, session_id: str) -> Optional[dict]:
        """Mark a session as archived."""
        session = self.get(session_id)
        if session is None:
            return None
        session["status"] = "archived"
        self.save(session)
        return self.get(session_id)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session_id: str) -> Optional[dict]:
        """Return a session dict, or None if not found."""
        path = self._path_for(session_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = yaml.safe_load(f)
        if data.get("turns") is None:
            data["turns"] = []
        return data

    def list_all(self) -> list:
        """Return all sessions sorted by ID (most recent last)."""
        if not self._dir.exists():
            return []
        sessions = []
        for path in sorted(self._dir.glob("SES-*.yaml")):
            with open(path) as f:
                data = yaml.safe_load(f)
            if data.get("turns") is None:
                data["turns"] = []
            sessions.append(data)
        return sessions

    def list_active(self) -> list:
        """Return sessions with status == 'active'."""
        return [s for s in self.list_all() if s.get("status") == "active"]

    def create(
        self,
        title: Optional[str] = None,
        context_snapshot: Optional[dict] = None,
        when: Optional[datetime.date] = None,
    ) -> dict:
        """Create and persist a new session. Returns the saved session."""
        session_id = self.next_id(when=when)
        session = make_session(session_id, title=title, context_snapshot=context_snapshot)
        self.save(session)
        return self.get(session_id)
