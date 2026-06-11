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
    → return response

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import sys
from pathlib import Path
from typing import Optional

from session import SessionStore, make_turn
from context import assemble_context, build_stores
from dispatch import dispatch

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


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
    ) -> None:
        self._session_store = session_store or SessionStore()
        self._stores = stores if stores is not None else build_stores()
        self._gateway = gateway

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
