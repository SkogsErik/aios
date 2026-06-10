"""
audit_log.py — Gateway audit log writer

Appends a structured JSON entry to the audit log for every model call.
The audit log is the primary accountability artefact for AI model usage
as required by ADR-002 (Model Gateway Pattern).

Each entry is one JSON object per line (JSONL format).
Schema: platform/model-gateway/schema/audit-log-schema.yaml

Capability: CAP-003 (AI and Model Management)
Defined by: ADR-006 — Model Gateway Technology Selection
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Thread lock to prevent interleaved writes from concurrent callers
_write_lock = threading.Lock()


def _next_call_id(log_path: Path) -> str:
    """Return the next sequential call ID by counting existing lines in the log."""
    if not log_path.exists():
        return "gw-0001"
    with log_path.open("r", encoding="utf-8") as f:
        count = sum(1 for line in f if line.strip())
    return f"gw-{count + 1:04d}"


def write_entry(
    log_path: Path,
    *,
    caller_id: str,
    model: str,
    status: str,
    latency_ms: int,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    cost_usd: Optional[float] = None,
    error: Optional[str] = None,
    context: Optional[dict] = None,
    prompt_preview: Optional[str] = None,
    completion_preview: Optional[str] = None,
) -> str:
    """
    Append one audit entry to the log file.

    Returns the call_id assigned to this entry.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    provider = model.split("/")[0] if "/" in model else "unknown"

    with _write_lock:
        call_id = _next_call_id(log_path)
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "call_id": call_id,
            "caller_id": caller_id,
            "model": model,
            "provider": provider,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "status": status,
            "error": error,
            "context": context,
            "prompt_preview": prompt_preview,
            "completion_preview": completion_preview,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return call_id


def read_entries(log_path: Path) -> list[dict]:
    """Return all audit entries from the log as a list of dicts."""
    if not log_path.exists():
        return []
    entries = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def tail_entries(log_path: Path, n: int = 20) -> list[dict]:
    """Return the last n audit entries."""
    return read_entries(log_path)[-n:]


def filter_entries(log_path: Path, caller_id: str | None = None,
                   status: str | None = None) -> list[dict]:
    """Return entries matching the given filters."""
    entries = read_entries(log_path)
    if caller_id:
        entries = [e for e in entries if e.get("caller_id") == caller_id]
    if status:
        entries = [e for e in entries if e.get("status") == status]
    return entries
