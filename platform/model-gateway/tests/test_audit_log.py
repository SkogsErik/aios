"""
test_audit_log.py — Tests for the audit log module.
"""

import json

import pytest

import audit_log as audit_mod


# ---------------------------------------------------------------------------
# write_entry / read_entries
# ---------------------------------------------------------------------------

def test_write_creates_log_file(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="test", model="ollama/llama3.2",
                          status="success", latency_ms=100)
    assert log.exists()


def test_write_produces_valid_json(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="WF-001", model="ollama/llama3.2",
                          status="success", latency_ms=200, total_tokens=42)
    entries = audit_mod.read_entries(log)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["caller_id"] == "WF-001"
    assert entry["model"] == "ollama/llama3.2"
    assert entry["status"] == "success"
    assert entry["total_tokens"] == 42
    assert entry["latency_ms"] == 200


def test_write_assigns_sequential_call_ids(tmp_path):
    log = tmp_path / "audit.jsonl"
    for _ in range(3):
        audit_mod.write_entry(log, caller_id="test", model="ollama/llama3.2",
                              status="success", latency_ms=10)
    entries = audit_mod.read_entries(log)
    assert [e["call_id"] for e in entries] == ["gw-0001", "gw-0002", "gw-0003"]


def test_write_extracts_provider_from_model(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="test", model="openai/gpt-4o",
                          status="success", latency_ms=300)
    entries = audit_mod.read_entries(log)
    assert entries[0]["provider"] == "openai"


def test_write_stores_context(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="WF-001", model="ollama/llama3.2",
                          status="success", latency_ms=50,
                          context={"asset_id": "KA-042"})
    entries = audit_mod.read_entries(log)
    assert entries[0]["context"] == {"asset_id": "KA-042"}


def test_write_records_error(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="test", model="ollama/llama3.2",
                          status="error", latency_ms=50, error="Connection refused")
    entries = audit_mod.read_entries(log)
    assert entries[0]["status"] == "error"
    assert entries[0]["error"] == "Connection refused"


def test_read_entries_empty_log(tmp_path):
    log = tmp_path / "audit.jsonl"
    assert audit_mod.read_entries(log) == []


def test_read_entries_missing_log(tmp_path):
    assert audit_mod.read_entries(tmp_path / "nonexistent.jsonl") == []


# ---------------------------------------------------------------------------
# tail_entries
# ---------------------------------------------------------------------------

def test_tail_returns_last_n(tmp_path):
    log = tmp_path / "audit.jsonl"
    for i in range(10):
        audit_mod.write_entry(log, caller_id=f"c-{i}", model="ollama/llama3.2",
                              status="success", latency_ms=i)
    tail = audit_mod.tail_entries(log, n=3)
    assert len(tail) == 3
    assert tail[-1]["caller_id"] == "c-9"


# ---------------------------------------------------------------------------
# filter_entries
# ---------------------------------------------------------------------------

def test_filter_by_caller_id(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="WF-001", model="ollama/llama3.2",
                          status="success", latency_ms=10)
    audit_mod.write_entry(log, caller_id="WF-002", model="ollama/llama3.2",
                          status="success", latency_ms=10)
    results = audit_mod.filter_entries(log, caller_id="WF-001")
    assert len(results) == 1
    assert results[0]["caller_id"] == "WF-001"


def test_filter_by_status(tmp_path):
    log = tmp_path / "audit.jsonl"
    audit_mod.write_entry(log, caller_id="test", model="ollama/llama3.2",
                          status="success", latency_ms=10)
    audit_mod.write_entry(log, caller_id="test", model="ollama/llama3.2",
                          status="error", latency_ms=5, error="Fail")
    errors = audit_mod.filter_entries(log, status="error")
    assert len(errors) == 1
    assert errors[0]["status"] == "error"
