"""
api.py — FastAPI HTTP server for the Conductor.

Binds to localhost only. No authentication (single-operator, local-first).
Serves the web UI from ../web/index.html.

Endpoints:
  POST /sessions              — create a new session
  GET  /sessions              — list sessions
  GET  /sessions/{id}         — get session details
  POST /sessions/{id}/chat    — send a message, get a response
  POST /sessions/{id}/archive — archive a session

  GET  /                      — serve the web UI

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from conductor import Conductor

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AIOS Conductor",
    description="Conversational interface for the AIOS personal AI operating system.",
    version="0.1.0",
)

# Single Conductor instance shared by all requests
_conductor = Conductor()


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the minimal web UI."""
    html_path = _WEB_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>AIOS Conductor</h1><p>Web UI not found.</p>")
    return HTMLResponse(html_path.read_text())


@app.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new conversation session."""
    session = _conductor.create_session(title=request.title)
    return {"session": _slim_session(session)}


@app.get("/sessions")
async def list_sessions(active_only: bool = True):
    """List sessions."""
    sessions = _conductor.list_sessions(active_only=active_only)
    return {"sessions": [_slim_session(s) for s in sessions]}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full session details including all turns."""
    session = _conductor.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"session": session}


@app.post("/sessions/{session_id}/chat")
async def chat(session_id: str, request: ChatRequest):
    """Send a message to the conductor within a session."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = _conductor.chat(session_id, request.message)
    return result


@app.post("/sessions/{session_id}/archive")
async def archive_session(session_id: str):
    """Archive a session."""
    session = _conductor.archive_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"session": _slim_session(session)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slim_session(session: dict) -> dict:
    """Return a session summary (without full turn content) for list views."""
    return {
        "id": session.get("id"),
        "title": session.get("title"),
        "status": session.get("status"),
        "created": session.get("created"),
        "updated": session.get("updated"),
        "turn_count": len(session.get("turns") or []),
    }


# ---------------------------------------------------------------------------
# Entry point (direct run)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
        log_level="info",
    )
