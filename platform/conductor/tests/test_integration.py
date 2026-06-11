"""
test_integration.py — Integration tests for the Conductor HTTP API.

Tests the full stack: FastAPI routes → Conductor → Session/Context/Dispatch → Tools.
The model gateway is mocked (no live model required).
All stores use temporary directories (no production data touched).

Run from repo root:
  PYTHONPATH=platform/conductor/src:wyrd/src \
    python3 -m pytest platform/conductor/tests/test_integration.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "platform" / "conductor" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "wyrd" / "src"))

# ---------------------------------------------------------------------------
# Mock gateway
# ---------------------------------------------------------------------------


class _MockGatewayResponse:
    def __init__(self, content):
        self.content = content


class _MockGateway:
    """Gateway that returns a canned response and records calls."""

    def __init__(self, response_text="mock model response"):
        self.response_text = response_text
        self.calls = []

    def complete(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        return _MockGatewayResponse(self.response_text)


# ---------------------------------------------------------------------------
# App factory (isolated store dirs per test)
# ---------------------------------------------------------------------------


def _make_test_app(tmp_path, gateway_response="mock model response"):
    """
    Build a FastAPI TestClient backed by isolated tmp stores and a mock gateway.
    """
    from fastapi.testclient import TestClient
    from session import SessionStore
    from conductor import Conductor
    import api as api_module

    sessions_dir = tmp_path / "sessions"
    mock_gw = _MockGateway(gateway_response)

    conductor = Conductor(
        session_store=SessionStore(base_dir=sessions_dir),
        stores={},   # empty Wyrd stores (no persona/project data)
        gateway=mock_gw,
    )

    # Monkey-patch the module-level conductor used by route handlers
    api_module._conductor = conductor

    client = TestClient(api_module.app, raise_server_exceptions=True)
    return client, mock_gw


# ===========================================================================
# Health / web UI
# ===========================================================================


class TestWebUI:
    def test_root_returns_html(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "AIOS" in r.text


# ===========================================================================
# Session lifecycle
# ===========================================================================


class TestSessionCreate:
    def test_create_session_no_title(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.post("/sessions", json={})
        assert r.status_code == 200
        data = r.json()
        assert "session" in data
        assert data["session"]["status"] == "active"
        assert data["session"]["id"].startswith("SES-")

    def test_create_session_with_title(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.post("/sessions", json={"title": "My session"})
        assert r.status_code == 200
        assert r.json()["session"]["title"] == "My session"

    def test_create_session_has_zero_turns(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.post("/sessions", json={})
        assert r.json()["session"]["turn_count"] == 0


class TestSessionList:
    def test_list_sessions_empty(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.get("/sessions")
        assert r.status_code == 200
        assert r.json()["sessions"] == []

    def test_list_sessions_returns_created(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        client.post("/sessions", json={"title": "A"})
        client.post("/sessions", json={"title": "B"})
        r = client.get("/sessions")
        assert len(r.json()["sessions"]) == 2

    def test_list_active_only_excludes_archived(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        s1 = client.post("/sessions", json={"title": "Keep"}).json()["session"]["id"]
        s2 = client.post("/sessions", json={"title": "Archive me"}).json()["session"]["id"]
        client.post(f"/sessions/{s2}/archive")
        r = client.get("/sessions?active_only=true")
        ids = [s["id"] for s in r.json()["sessions"]]
        assert s1 in ids
        assert s2 not in ids

    def test_list_all_includes_archived(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        s1 = client.post("/sessions", json={}).json()["session"]["id"]
        client.post(f"/sessions/{s1}/archive")
        r = client.get("/sessions?active_only=false")
        assert len(r.json()["sessions"]) == 1


class TestSessionGet:
    def test_get_existing_session(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        created = client.post("/sessions", json={"title": "Test"}).json()["session"]
        r = client.get(f"/sessions/{created['id']}")
        assert r.status_code == 200
        assert r.json()["session"]["id"] == created["id"]
        assert "turns" in r.json()["session"]

    def test_get_missing_session_404(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.get("/sessions/SES-2099-0101-001")
        assert r.status_code == 404


class TestSessionArchive:
    def test_archive_session(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        sid = client.post("/sessions", json={}).json()["session"]["id"]
        r = client.post(f"/sessions/{sid}/archive")
        assert r.status_code == 200
        assert r.json()["session"]["status"] == "archived"

    def test_archive_missing_session_404(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        r = client.post("/sessions/SES-2099-0101-001/archive")
        assert r.status_code == 404


# ===========================================================================
# Chat endpoint
# ===========================================================================


class TestChat:
    def _create_session(self, client):
        return client.post("/sessions", json={}).json()["session"]["id"]

    def test_chat_returns_response(self, tmp_path):
        client, gw = _make_test_app(tmp_path, gateway_response="Here is the answer")
        sid = self._create_session(client)
        r = client.post(f"/sessions/{sid}/chat", json={"message": "What is Python?"})
        assert r.status_code == 200
        data = r.json()
        assert data["response"] == "Here is the answer"
        assert data["session_id"] == sid

    def test_chat_returns_intent(self, tmp_path):
        client, gw = _make_test_app(tmp_path)
        sid = self._create_session(client)
        r = client.post(f"/sessions/{sid}/chat", json={"message": "What is AIOS?"})
        assert r.json()["intent"] == "research"  # fast-path: "What is"

    def test_chat_persists_turns(self, tmp_path):
        client, gw = _make_test_app(tmp_path)
        sid = self._create_session(client)
        client.post(f"/sessions/{sid}/chat", json={"message": "Hello"})
        session = client.get(f"/sessions/{sid}").json()["session"]
        # 2 turns: user + assistant
        assert len(session["turns"]) == 2
        assert session["turns"][0]["role"] == "user"
        assert session["turns"][1]["role"] == "assistant"

    def test_chat_turn_index_increments(self, tmp_path):
        client, gw = _make_test_app(tmp_path)
        sid = self._create_session(client)
        r1 = client.post(f"/sessions/{sid}/chat", json={"message": "First"})
        r2 = client.post(f"/sessions/{sid}/chat", json={"message": "Second"})
        assert r1.json()["turn_index"] == 0
        assert r2.json()["turn_index"] == 1

    def test_chat_empty_message_400(self, tmp_path):
        client, _ = _make_test_app(tmp_path)
        sid = self._create_session(client)
        r = client.post(f"/sessions/{sid}/chat", json={"message": "  "})
        assert r.status_code == 400

    def test_chat_creates_session_if_missing(self, tmp_path):
        client, gw = _make_test_app(tmp_path)
        # Chat to a non-existent session ID — conductor creates it
        r = client.post("/sessions/SES-2099-0101-001/chat", json={"message": "Hi"})
        assert r.status_code == 200
        # A new session was created (different ID)
        assert r.json()["session_id"] != "SES-2099-0101-001"

    def test_chat_calls_gateway(self, tmp_path):
        client, gw = _make_test_app(tmp_path)
        sid = self._create_session(client)
        client.post(f"/sessions/{sid}/chat", json={"message": "Explain TCP"})
        assert len(gw.calls) >= 1

    def test_chat_multi_turn_coherence(self, tmp_path):
        client, gw = _make_test_app(tmp_path, gateway_response="response")
        sid = self._create_session(client)
        client.post(f"/sessions/{sid}/chat", json={"message": "First question"})
        client.post(f"/sessions/{sid}/chat", json={"message": "Second question"})
        session = client.get(f"/sessions/{sid}").json()["session"]
        assert len(session["turns"]) == 4  # 2 user + 2 assistant

    def test_chat_plan_intent(self, tmp_path):
        client, gw = _make_test_app(tmp_path, gateway_response="plan output")
        sid = self._create_session(client)
        r = client.post(f"/sessions/{sid}/chat", json={"message": "Help me plan my release"})
        assert r.json()["intent"] == "plan"

    def test_chat_summarise_intent(self, tmp_path):
        client, gw = _make_test_app(tmp_path, gateway_response="summary")
        sid = self._create_session(client)
        r = client.post(f"/sessions/{sid}/chat", json={"message": "Summarise the discussion"})
        assert r.json()["intent"] == "summarise"

    def test_chat_tool_recorded_on_turn(self, tmp_path):
        client, gw = _make_test_app(tmp_path)
        sid = self._create_session(client)
        client.post(f"/sessions/{sid}/chat", json={"message": "What is Docker?"})
        session = client.get(f"/sessions/{sid}").json()["session"]
        assistant_turn = session["turns"][1]
        assert assistant_turn["tool"] == "research"
