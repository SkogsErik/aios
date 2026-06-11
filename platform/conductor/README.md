# Conductor

> DOC-020 | Runtime C — Conversational interface for AIOS

The Conductor is the interactive layer of AIOS. It gives you a natural-language interface to direct the system — ask questions, request plans, summarise information — without requiring you to know which CLI command or workflow to invoke.

**Design:** [ADR-013 — Conductor Agent Design](../../adr/0013-conductor-agent-design.md)  
**Capability:** CAP-017  
**Runtime:** C (alongside Runtime A: Workflow Executor and Runtime B: Executive Daemon)

---

## What the Conductor does

| You say | Conductor does |
|---|---|
| "What is X?" | Researches X using the model gateway with your personal context injected |
| "Plan a migration to Postgres" | Generates a numbered, actionable plan |
| "Summarise our conversation" | Extracts key points and action items |
| Anything else | Responds as a context-aware assistant |

All responses are grounded in your Wyrd context: active projects, goals, focus areas, and persona — making responses relevant to your actual situation, not generic.

---

## Quick start

```bash
# Install dependencies
pip3 install --break-system-packages -r platform/conductor/requirements.txt

# Ensure model gateway is configured (platform/model-gateway/)

# Start the conductor
cd platform/conductor/src
PYTHONPATH=.:../../../wyrd/src:../../executive-daemon/src:../../model-gateway/src \
  python3 api.py

# Open in browser
open http://localhost:8080
```

---

## Directory structure

```
platform/conductor/
├── src/
│   ├── conductor.py      # Orchestration: session → context → dispatch → respond
│   ├── session.py        # Session CRUD and conversation history (YAML persistence)
│   ├── context.py        # Wyrd context assembly for model call injection
│   ├── dispatch.py       # Intent classification and tool routing
│   ├── tools/
│   │   ├── research.py   # Research tool: context-injected information queries
│   │   ├── plan.py       # Plan tool: structured, numbered plan generation
│   │   ├── summarise.py  # Summarise tool: key-point extraction
│   │   └── converse.py   # Converse tool: general multi-turn conversation
│   └── api.py            # FastAPI HTTP server (localhost:8080)
├── web/
│   └── index.html        # Minimal single-page chat UI (no build step)
├── tests/
│   ├── test_session.py   # 26 session store tests
│   ├── test_dispatch.py  # 21 intent classification and dispatch tests
│   └── test_context.py   # 13 context assembly tests
├── requirements.txt
└── README.md             # This file (DOC-020)
```

---

## Sessions

Each conversation is a **session** — a persisted YAML file at:
```
platform/knowledge/sessions/SES-YYYY-MMDD-NNN.yaml
```

Sessions follow the ADR-003 storage pattern. Every turn is appended to the session file, creating a complete, inspectable conversation log.

Session turns are also written as observations (source: `conductor`) feeding the Wyrd learning engine. Conductor usage becomes self-documenting.

---

## Context injection

Before every model call, the Conductor assembles a context block from Wyrd stores:

```
=== AIOS Context ===
Operator: <name>
Values:   <declared values>
Active projects:
  - PRJ-001 [active] AIOS Core
  - PRJ-002 [active] Conductor
Active goals:
  - GL-001 Ship AIOS v1
Focus areas:
  - FCA-001 Engineering [primary]
===================
```

The richer your Wyrd data, the more personalised and contextual the responses.

---

## Tool routing

Intent is classified using a keyword fast-path (no model call) followed by a lightweight model classification call if the fast-path is inconclusive:

| Intent class | Examples |
|---|---|
| `research` | "What is X?", "Explain Y", "How does Z work?" |
| `plan` | "Plan X", "Steps for Y", "Strategy for Z" |
| `summarise` | "Summarise", "TL;DR", "Key points" |
| `converse` | Everything else |

---

## HTTP API

| Method | Path | Description |
|---|---|---|
| `POST` | `/sessions` | Create a new session |
| `GET` | `/sessions` | List sessions |
| `GET` | `/sessions/{id}` | Get session with full turn history |
| `POST` | `/sessions/{id}/chat` | Send a message, receive a response |
| `POST` | `/sessions/{id}/archive` | Archive a session |
| `GET` | `/` | Web UI |

---

## Running tests

```bash
# From repo root
PYTHONPATH=platform/conductor/src python3 -m pytest platform/conductor/tests/ -q
```

---

## Design principles

- **Local-first.** HTTP server binds to `localhost` only. No external service dependencies.
- **Gateway-only.** All model calls flow through `platform/model-gateway/` (ADR-002). The conductor never calls a provider directly.
- **Inspectable.** Sessions are YAML files. Every turn is readable without tooling.
- **Bounded.** The conductor does not modify canonical persona or project data. It reads Wyrd; it does not write to it.
- **Wyrd-integrated.** Conductor usage becomes observations, feeding the learning engine and strengthening the persona model over time.

---

## What's deferred

- **Signal / notifications:** Output-only notification channel planned for a later phase.
- **Agent teams:** Multi-agent coordination deferred to Phase 7+. The `execute` tool class is reserved.
- **Authentication:** Not needed at Phase 6 (single-operator, local-only).

---

## Related

- [ADR-013 — Conductor Agent Design](../../adr/0013-conductor-agent-design.md)
- [ADR-012 — Wyrd Subsystem Boundary](../../adr/0012-wyrd-subsystem-boundary.md)
- [ADR-002 — Model Gateway Pattern](../../adr/0002-model-gateway-pattern.md)
- [ADR-003 — Knowledge Persistence Approach](../../adr/0003-knowledge-persistence-approach.md)
- [ADR-008 — Observation Store Architecture](../../adr/0008-observation-store-architecture.md)
- [Wyrd README](../../wyrd/README.md)
