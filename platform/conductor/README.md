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
| "Plan a migration to Postgres" | Generates a numbered, actionable plan and executes it via agent roles |
| "Summarise our conversation" | Extracts key points and action items |
| "Write a script to ..." | Delegates to a coder agent with file-read/write/shell tools |
| "Search the web for ..." | Delegates to a researcher agent with web-search and read-file tools |
| Anything else | Responds as a context-aware assistant |

Multi-step goals are decomposed into a plan: the Conductor assigns each step to the right agent role (researcher, coder, synthesizer), executes them sequentially, and passes results between steps. All agent actions are governed by role-based tool access and operator-defined checkpoints.

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
│   ├── react.py          # ReAct loop: reasoning-observing-acting for single-goal tasks
│   ├── orchestrator.py   # Plan decomposition, step execution, result accumulation
│   ├── task_store.py     # Task lifecycle persistence (TSK-* YAML files)
│   ├── agents.py         # Role registry: declarative YAML role definitions with tool access
│   ├── agents/
│   │   ├── researcher.yaml    # read_file, web_search
│   │   ├── coder.yaml         # read_file, write_file, run_shell
│   │   └── synthesizer.yaml   # read_file only
│   ├── tools/
│   │   ├── base.py        # BaseTool, ToolResult, ToolCall
│   │   ├── registry.py    # ToolRegistry, ToolExecutor (param validation, role enforcement)
│   │   ├── execute.py     # Single-step tool execution wrapper
│   │   ├── read_file.py   # Path-restricted file reader
│   │   ├── write_file.py  # Path-restricted writer (requires operator confirmation)
│   │   ├── run_shell.py   # Output-only shell (blocks interactive commands)
│   │   ├── web_search.py  # Web search via duckduckgo_search library
│   │   ├── research.py    # Research tool: context-injected information queries
│   │   ├── plan.py        # Plan tool: structured, numbered plan generation
│   │   ├── summarise.py   # Summarise tool: key-point extraction
│   │   └── converse.py    # Converse tool: general multi-turn conversation
│   └── api.py            # FastAPI HTTP server (localhost:8080)
├── web/
│   └── index.html        # Minimal single-page chat UI (no build step)
├── tests/
│   ├── test_session.py       # 26 session store tests
│   ├── test_dispatch.py      # 21 intent classification tests
│   ├── test_context.py       # 13 context assembly tests
│   ├── test_react.py         # 13 ReAct loop tests
│   ├── test_orchestrator.py  # 27 orchestrator tests
│   ├── test_task_store.py    # 21 task store tests
│   ├── test_agents.py        # 14 role registry tests
│   ├── test_tools_*.py       # 60+ tests across all tool modules
│   ├── test_conductor_tasks.py # 18 conductor task tests
│   └── test_integration.py   # 10 integration tests
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
| `POST` | `/plans` | Create a plan from a goal (decomposes into steps) |
| `POST` | `/plans/{id}/execute` | Execute a plan sequentially |
| `GET` | `/plans/{id}` | Get plan with step statuses |
| `GET` | `/` | Web UI |

---

## Running tests

```bash
# From repo root
PYTHONPATH=platform/conductor/src python3 -m pytest platform/conductor/tests/ -q
```

212 tests across all conductor modules.

## Design principles

- **Local-first.** HTTP server binds to `localhost` only. No external service dependencies.
- **Gateway-only.** All model calls flow through `platform/model-gateway/` (ADR-002). The conductor never calls a provider directly.
- **Inspectable.** Sessions are YAML files. Every turn is readable without tooling.
- **Bounded.** The conductor does not modify canonical persona or project data. It reads Wyrd; it does not write to it.
- **Wyrd-integrated.** Conductor usage becomes observations, feeding the learning engine and strengthening the persona model over time.
- **Governed autonomy.** Agent tool access is enforced by role definitions; operator confirmation gates block high-impact actions.

---

## Related

- [ADR-013 — Conductor Agent Design](../../adr/0013-conductor-agent-design.md)
- [ADR-014 — Agent Tool Interface](../../adr/0014-agent-tool-interface.md)
- [ADR-015 — Agent Role Model](../../adr/0015-agent-role-model.md)
- [ADR-016 — Orchestration Pattern](../../adr/0016-orchestration-pattern.md)
- [ADR-012 — Wyrd Subsystem Boundary](../../adr/0012-wyrd-subsystem-boundary.md)
- [ADR-002 — Model Gateway Pattern](../../adr/0002-model-gateway-pattern.md)
- [ADR-003 — Knowledge Persistence Approach](../../adr/0003-knowledge-persistence-approach.md)
- [ADR-008 — Observation Store Architecture](../../adr/0008-observation-store-architecture.md)
- [Wyrd README](../../wyrd/README.md)
