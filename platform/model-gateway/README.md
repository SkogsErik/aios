# Model Gateway — Phase 4

**Capability:** CAP-003 (AI and Model Management)  
**Phase:** 4 — Runtime and Workflow Baseline  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

This directory contains the Phase 4 implementation of the AIOS Model Gateway (Layer 3). It mediates all AI model access, ensuring that:

- Every model call is audited (who called, what was sent, what was returned)
- Provider and model are configurable without code changes
- Rate limits and cost budgets are enforced
- Safety pre- and post-filtering is applied uniformly
- No platform component can call an AI model by bypassing this gateway

Technology choices are documented in [ADR-006](../../adr/0006-model-gateway-technology.md) (LiteLLM + Python module) and [ADR-002](../../adr/0002-model-gateway-pattern.md) (gateway pattern).

---

## Directory layout

```
platform/model-gateway/
  config/
    gateway-config.yaml       # Active gateway configuration
  schema/
    gateway-config-schema.yaml
    audit-log-schema.yaml
  src/
    gateway.py                # Core module: complete(), audit logging, rate limiting
    config_loader.py          # Configuration loading and validation
    audit_log.py              # Audit log writer
    cli.py                    # CLI: query, audit commands
  audit/
    audit.jsonl               # Append-only audit log (not committed)
  tests/
    conftest.py
    test_gateway.py
    test_audit_log.py
  docs/
    gateway-runbook.md
  requirements.txt
```

---

## Installation

```bash
cd platform/model-gateway
pip install -r requirements.txt
```

---

## Configuration

The gateway is configured via `config/gateway-config.yaml`. Copy the sample and edit:

```bash
cp config/gateway-config.yaml.sample config/gateway-config.yaml
```

Key fields:

| Field | Description |
|---|---|
| `default_model` | Default model identifier (e.g. `ollama/llama3.2`) |
| `providers` | Provider configurations (API base URL, etc.) |
| `rate_limit.requests_per_minute` | Maximum requests per minute |
| `cost.max_usd_per_day` | Daily cost budget in USD (0 = unlimited) |
| `safety.enabled` | Enable basic safety filtering |
| `audit.log_path` | Path to the audit log file |

Provider API keys are **not** stored in this file. They are loaded from environment variables (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

---

## Usage

### Python module (primary interface)

```python
from gateway import complete

response = complete(
    prompt="Summarise this document in three sentences.",
    caller_id="WF-001",
    context={"asset_id": "KA-042"},
)
print(response["content"])
```

### CLI

```bash
# Send a completion request
python src/cli.py query "Explain the AIOS knowledge governance model."

# View recent audit entries
python src/cli.py audit tail

# View audit entries for a specific caller
python src/cli.py audit filter --caller WF-001
```

---

## Audit log

Every model call produces an entry in `audit/audit.jsonl`. Each entry is a single JSON object:

```json
{
  "timestamp": "2026-06-10T09:00:00Z",
  "call_id": "gw-0001",
  "caller_id": "WF-001",
  "model": "ollama/llama3.2",
  "provider": "ollama",
  "prompt_tokens": 42,
  "completion_tokens": 128,
  "total_tokens": 170,
  "cost_usd": 0.0,
  "latency_ms": 1240,
  "status": "success",
  "error": null
}
```

Prompt and completion text are **not** stored in the audit log by default (to avoid sensitive data retention). Enable content logging explicitly in config if required.

---

## Running tests

```bash
cd platform/model-gateway
python -m pytest tests/ -v
```

Tests use a stub provider and do not require a running model server or API key.

---

## Related artifacts

- [ADR-002 — Model Gateway Pattern](../../adr/0002-model-gateway-pattern.md)
- [ADR-006 — Model Gateway Technology Selection](../../adr/0006-model-gateway-technology.md)
- [Capability Map — CAP-003](../../architecture/capability-map.md)
- [Governance Model — AI and Model Governance](../../governance/governance-model.md)
