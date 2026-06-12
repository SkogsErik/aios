"""
conductor.py — Conductor orchestration layer.

Ties together: session management, context assembly, intent dispatch, and
observation writing. This is the main entry point for processing operator messages.

Flow:
  receive message
    → load or create session
    → assemble Wyrd context
    → dispatch (classify intent → route to tool)
    → append turn to session
    → persist turns as observations
    → return response

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import datetime
import sys
from pathlib import Path
from typing import Optional

import yaml

from session import SessionStore, make_turn
from context import assemble_context, build_stores
from dispatch import dispatch

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_OBS_DIR = _REPO_ROOT / "platform" / "knowledge" / "observations"


class Conductor:
    """
    Main conductor orchestrator. One instance per server process.

    Parameters
    ----------
    session_store : SessionStore, optional
        Injectable for testing.
    stores : dict, optional
        Dict of Wyrd stores (persona_store, project_store, goal_store, focus_store).
        Loaded from defaults if not provided.
    gateway : module, optional
        Gateway module (injectable for testing).
    """

    def __init__(
        self,
        session_store: Optional[SessionStore] = None,
        stores: Optional[dict] = None,
        gateway=None,
        obs_dir: Optional[Path] = None,
    ) -> None:
        self._session_store = session_store or SessionStore()
        self._stores = stores if stores is not None else build_stores()
        self._gateway = gateway
        self._obs_dir = obs_dir or _OBS_DIR
        self._obs_id_cache: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def create_session(self, title: Optional[str] = None) -> dict:
        """Create a new conversation session, capturing a Wyrd context snapshot."""
        context_block = self._build_context()
        snapshot = {"context_block": context_block}
        return self._session_store.create(title=title, context_snapshot=snapshot)

    def get_session(self, session_id: str) -> Optional[dict]:
        """Return a session dict by ID."""
        return self._session_store.get(session_id)

    def list_sessions(self, active_only: bool = True) -> list:
        """Return sessions."""
        if active_only:
            return self._session_store.list_active()
        return self._session_store.list_all()

    def archive_session(self, session_id: str) -> Optional[dict]:
        """Archive a session."""
        return self._session_store.archive(session_id)

    # ------------------------------------------------------------------
    # Message processing
    # ------------------------------------------------------------------

    def chat(self, session_id: str, message: str) -> dict:
        """
        Process an operator message within a session.

        Creates the session if it does not exist.

        Parameters
        ----------
        session_id : str
            The session to add this message to.
        message : str
            The operator's message.

        Returns
        -------
        dict with keys:
            session_id  — str
            intent      — classified tool
            response    — model response text
            turn_index  — index of this turn (0-based user message index)
        """
        session = self._session_store.get(session_id)
        if session is None:
            session = self._session_store.create(
                title=message[:60],
                context_snapshot={"context_block": self._build_context()},
            )
            session_id = session["id"]

        history = session.get("turns") or []
        context_block = (
            session.get("context_snapshot", {}).get("context_block")
            or self._build_context()
        )

        # Dispatch to tool
        result = dispatch(
            message,
            context_block,
            history,
            gateway=self._gateway,
        )

        # Persist operator turn
        user_turn = make_turn("user", message)
        self._session_store.add_turn(session_id, user_turn)

        # Persist assistant turn
        assistant_turn = make_turn("assistant", result["response"], tool=result["tool"])
        self._session_store.add_turn(session_id, assistant_turn)

        # Record both turns as observations
        self._save_turn_as_observation(session_id, "user", message)
        self._save_turn_as_observation(
            session_id, "assistant", result["response"], tool=result["tool"]
        )

        # Count user turns for turn_index
        turn_index = sum(1 for t in history if t.get("role") == "user")

        return {
            "session_id": session_id,
            "intent": result["intent"],
            "response": result["response"],
            "turn_index": turn_index,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_context(self) -> str:
        return assemble_context(
            persona_store=self._stores.get("persona_store"),
            project_store=self._stores.get("project_store"),
            goal_store=self._stores.get("goal_store"),
            focus_store=self._stores.get("focus_store"),
        )

    # ------------------------------------------------------------------
    # Observation recording
    # ------------------------------------------------------------------

    def _next_observation_id(self, date_str: str) -> str:
        """Return the next available OBS-NNN id for the given date string (YYYYMMDD)."""
        cache_key = f"{date_str}"
        if cache_key not in self._obs_id_cache:
            obs_file = self._obs_dir / f"{date_str[:4]}/{date_str[4:6]}/{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}.yaml"
            max_counter = 0
            if obs_file.exists():
                with open(obs_file) as f:
                    records = yaml.safe_load(f) or []
                for r in records:
                    oid = r.get("id", "")
                    if oid.startswith(f"OBS-{date_str}-"):
                        try:
                            counter = int(oid.split("-")[-1])
                            max_counter = max(max_counter, counter)
                        except (ValueError, IndexError):
                            pass
            self._obs_id_cache[cache_key] = max_counter
        self._obs_id_cache[cache_key] += 1
        return f"OBS-{date_str}-{self._obs_id_cache[cache_key]:03d}"

    def _save_turn_as_observation(
        self,
        session_id: str,
        role: str,
        content: str,
        tool: Optional[str] = None,
    ) -> None:
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        obs_file = self._obs_dir / now.strftime("%Y/%m") / f"{now.strftime('%Y-%m-%d')}.yaml"
        obs_file.parent.mkdir(parents=True, exist_ok=True)
        summary = content[:200] + ("..." if len(content) > 200 else "")
        tags = ["conductor", "conversation", role]
        if tool:
            tags.append(tool)
        entry = {
            "id": self._next_observation_id(date_str),
            "timestamp": now.isoformat(),
            "type": "note",
            "source_mechanism": "manual",
            "source_component": "conductor",
            "summary": f"[{session_id}] {role}: {summary}",
            "project": None,
            "energy": None,
            "tags": tags,
        }
        records: list[dict] = []
        if obs_file.exists():
            with open(obs_file) as f:
                records = yaml.safe_load(f) or []
        records.append(entry)
        with open(obs_file, "w") as f:
            yaml.dump(records, f, default_flow_style=False, sort_keys=False)
