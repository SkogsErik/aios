# 0013 — Conductor Agent Design

**ID:** ADR-013
**Status:** Accepted
**Date:** 2026-06-11
**Affects:** CAP-004, CAP-010, CAP-013, CAP-015, CAP-017, THEME-004, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

Through Phase 5 and the early Phase 6 sprint, AIOS has accumulated substantial infrastructure: a governed knowledge platform, a model gateway, a workflow runtime, an executive daemon with rules engine and learning engine, and the Wyrd identity subsystem (ADR-012).

The architecture has a structural gap: **there is no way for the operator to interact with the system in real time.** Every capability requires the operator to know which tool to invoke, with which arguments, at the command line. The executive daemon watches and records but does not respond. The knowledge platform stores but cannot be queried conversationally. The model gateway handles AI calls but has no first-class caller for operator-initiated tasks.

This means AIOS has very low day-to-day utility. A system that accumulates knowledge about you but cannot be asked a question has no immediate value. The operator cannot:

- Ask the system to research a concept
- Ask for a plan or analysis
- Initiate a multi-step task through natural language
- Get help from the system without manually composing CLI commands

The Wyrd subsystem (ADR-012) addresses long-term utility — building a deep model of the operator over time. But Wyrd's value compounds slowly. The gap between building Wyrd and deriving value from it is measured in weeks or months of data accumulation.

**A Conductor agent closes this gap immediately.** It provides an interface through which the operator can direct the system in natural language, today, without waiting for the persona model to mature.

---

### Relationship to ADR-005 (Workflow Executor)

ADR-005 established the workflow executor as a CLI-invoked, YAML-defined, governed execution engine for bounded, predetermined tasks. It is correct for its use case and is not superseded here.

The workflow executor is the wrong foundation for a Conductor because:

1. **Workflows are predetermined.** A conductor must decide what to do at runtime based on operator intent. YAML files cannot express this dynamism.
2. **Workflows are invoked, not conversational.** A conductor maintains session context across turns. A workflow starts, runs, and terminates.
3. **Workflows assume the operator knows the task.** A conductor helps the operator discover and define the task.

The conductor sits **above** the workflow executor in the stack. It may trigger governed workflows for well-defined subtasks (e.g., "ingest this document into the knowledge platform"), but it does not replace them. The workflow executor remains the correct mechanism for auditable, bounded, governed task execution.

---

### Relationship to ADR-010 (Two-Runtime Model)

ADR-010 defines two runtimes: Runtime A (workflow executor) and Runtime B (executive daemon). The conductor is a **third runtime** — not a replacement for either.

```
Runtime A: Workflow Executor   — governed, bounded, discrete tasks (ADR-005)
Runtime B: Executive Daemon    — continuous attention, rules, learning (ADR-010)
Runtime C: Conductor           — interactive, conversational, operator-directed (this ADR)
```

All three runtimes coexist and share the filesystem contract (ADR-003). The conductor reads from the knowledge platform and Wyrd stores. It does not write to daemon state and does not directly manage attention or priority.

---

## Decision

### Part 1: The Conductor is a first-class runtime

The Conductor (`platform/conductor/`) is introduced as a distinct platform module. It is a persistent HTTP service that the operator interacts with through a web interface (and later, other channels).

**The Conductor's responsibilities:**
- Receive operator messages (natural language instructions)
- Maintain conversation session context across turns
- Inject Wyrd context (persona, active projects, observations) into every model call
- Route operator intent to the correct tool (research, plan, summarise, execute)
- Delegate to the model gateway for all AI inference (Principle 2)
- Return structured, inspectable responses
- Persist conversation history as a knowledge asset (ADR-003, ADR-008)

**The Conductor does NOT:**
- Manage attention state or priority (that is the executive daemon)
- Execute governed workflows autonomously without operator confirmation
- Modify canonical persona data without operator review (Principle 7, ADR-007)
- Call models directly, bypassing the gateway (Principle 2)
- Spawn autonomous agent teams at this stage (deferred — see Part 5)

### Part 2: Communication channel — web-first

The initial operator interface is a local HTTP server with a minimal single-page web UI. This is not a product decision — it is the simplest inspectable interface that works.

**Rationale for web-first over Signal:**
- Web UI is fully operator-controlled (no external service dependency)
- Easier to debug, inspect, and extend
- Local-only by default (Principle 1 — local-first)
- Signal requires a separate registered number, `signal-cli` daemon, and unofficial API dependency
- Signal can be added later as an **output-only notification channel** (not as a primary input method) — this is explicitly planned as a later extension, not this phase

The web UI is intentionally minimal: a text input, a conversation history view, and nothing else. No framework dependencies. No build step. It runs from a single `index.html` file.

**Server:** FastAPI (already a dependency in the ecosystem; no new major dependency). Binds to `localhost` only. No authentication at Phase 6 (single-operator, local-only system).

### Part 3: Session model

A **session** is a named conversation with the conductor. Sessions have:
- A unique ID (`SES-YYYY-MMDD-NNN`)
- A conversation history (list of turns: role, content, timestamp)
- An associated context snapshot (persona state, active projects at session start)
- A status: `active`, `archived`

Sessions are persisted as YAML files at `platform/knowledge/sessions/SES-xxx.yaml`, consistent with ADR-003 (file-based, human-readable, version-controllable).

Each session turn is also written as an observation (OBS-NNN) with `source_mechanism: "conductor"`, making all conductor interactions part of the observation stream that feeds the learning engine. This is the integration point between the conductor and Wyrd — conductor usage becomes self-documenting.

**Context injection:** At the start of every model call, the conductor assembles a context block:
```
System context:
  Persona:    [declared values, active facts from PRS-001]
  Projects:   [active PRJ-NNN titles, status, health]
  Focus:      [top 3 priority items from rules engine output]
  Recent obs: [last 5 observations, summarised]
```

This context is prepended to every model call. It ensures the conductor reasons from the operator's actual situation, not generic reasoning.

### Part 4: Tool interface

The conductor routes operator intent to one of four built-in tools. Tools are thin wrappers — they assemble prompts, call the model gateway, and return structured results. They do not have autonomous execution authority.

| Tool | Intent class | What it does |
|---|---|---|
| `research` | "What is X?", "Explain Y", "Find out about Z" | Queries model gateway with context + optional knowledge platform retrieval; returns structured summary |
| `plan` | "Plan X", "How should I approach Y", "Help me design Z" | Generates a structured plan as a numbered list of steps with dependencies; operator can then execute steps manually or via workflow executor |
| `summarise` | "Summarise X", "TL;DR of Y", "What are the key points?" | Summarises a document, conversation history, or set of observations |
| `converse` | Everything else | General-purpose turn in a conversation; uses full context injection; returns a response |

A fifth tool class is **reserved** for future expansion:

| Tool | Intent class | Status |
|---|---|---|
| `execute` | "Do X", "Run Y", "Set up Z" | Reserved — Phase 7+. Will trigger governed workflows. Requires operator confirmation gate. |

**Intent classification** is handled by the model gateway (a lightweight classification call before the main call), not by rule-based parsing. The operator's intent is classified into one of the tool classes above before the tool is invoked.

### Part 5: Multi-agent team deferral

The request to "set up a team of agents to build a solution" is explicitly deferred to Phase 7 or later. This is an architectural decision, not a capability decision.

The reasons:

1. **Foundation first.** A conductor that can research, plan, and converse must work reliably before it coordinates multiple agents. Building agent teams before the conductor is stable creates a fragile foundation.
2. **Agent roles not yet defined.** The architecture names agent roles as a late-stage abstraction (Principle 6). Defining them now, before the conductor is operational, is premature.
3. **Governance.** Multi-agent coordination requires inter-agent communication protocols, result aggregation, conflict resolution, and audit trails that do not yet exist. Introducing them without governance is inconsistent with Principle 4.

Phase 7 will introduce **agent tool-use** — the conductor invokes specialised sub-agents (researcher, coder, planner) as tools with defined interfaces. This is architecturally distinct from full multi-agent orchestration, which remains Phase 8.

### Part 6: Autonomy scope

The conductor operates at **Autonomy Stage 2** (assisted, with operator review):

| Action | Autonomy |
|---|---|
| Research and summarise | Fully autonomous — no confirmation required |
| Generate a plan | Autonomous generation; operator decides whether to act on it |
| Trigger a governed workflow | Requires explicit operator confirmation in the conversation |
| Modify persona or project data | Not permitted; operator must use `aios` CLI commands |
| Spawn sub-agents | Not permitted in Phase 6 |

All model calls are logged through the model gateway (ADR-002). All session turns are persisted. No conductor action is invisible.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Dedicated conductor runtime, web-first (this decision)** | Clean separation; local-first; inspectable; consistent with existing patterns; immediately useful | Third runtime to maintain; FastAPI adds a process to manage |
| **Extend executive daemon to handle conversations** | Single process | Conflates attention management (continuous, background) with interactive conversation (event-driven, foreground); different lifecycle, different failure modes |
| **Extend workflow executor with conversational mode** | Single codebase | ADR-005 executor is designed for bounded, predetermined tasks; conversational mode requires dynamic dispatch; would corrupt the simplicity of the workflow executor |
| **Signal as primary interface** | Mobile-accessible; notification model is familiar | Unofficial API; external service dependency; breaks local-first; harder to inspect and debug |
| **Full multi-agent architecture from day one** | Immediately powerful | Premature abstraction; no stable conductor foundation to build on; governance requirements not yet defined |

---

## Rationale

The conductor pattern was chosen because:

- **It closes the utility gap immediately.** On day one, the operator can ask the conductor to research a concept, summarise a document, or help plan an approach. No data accumulation required.
- **It is coherent with the existing architecture.** It reads from Wyrd stores for context, delegates to the model gateway for inference, and persists sessions as observations. Every component already exists.
- **It is bounded.** The conductor does not execute autonomously, does not modify canonical data, and does not bypass the gateway. It is a well-governed assistant, not an autonomous agent.
- **It makes Wyrd immediately more valuable.** The richer the persona and observation history in Wyrd, the better the context the conductor has, and the more personalised and useful its responses. The two systems reinforce each other.
- **Web-first is the right starting point.** Local, inspectable, no external dependencies, easily extensible. Signal, TUI, and other channels can be added later once the core loop is proven.

---

## Consequences

**Positive:**
- AIOS has daily-use utility from the moment the conductor is running.
- Operator interactions become observations, feeding the learning engine automatically.
- The conductor serves as a testbed for the context injection and persona utility that Wyrd is building toward.
- The architecture gains a clean interaction layer (Layer 8) that was previously empty.

**Negative:**
- A third runtime to build, test, and maintain.
- FastAPI introduces a persistent HTTP process alongside the daemon.
- Session persistence adds another store to the knowledge platform.
- Context assembly on every call has a latency cost (mitigated by caching active state).

**Neutral:**
- The conductor does not change how the workflow executor or executive daemon work.
- Sessions are stored in `platform/knowledge/sessions/` consistent with ADR-003 — no new storage mechanism.
- Multi-agent capability is explicitly deferred; this decision does not foreclose it.

---

## Directory structure

```
platform/conductor/
├── src/
│   ├── conductor.py          # orchestration: session → context → dispatch → respond
│   ├── session.py            # session CRUD, conversation history, YAML persistence
│   ├── context.py            # context assembly from Wyrd stores + rules engine output
│   ├── dispatch.py           # intent classification + tool routing
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── research.py       # research tool: context-injected model query
│   │   ├── plan.py           # plan tool: structured plan generation
│   │   └── summarise.py      # summarise tool: document/observation summarisation
│   └── api.py                # FastAPI HTTP endpoint (localhost only)
├── web/
│   └── index.html            # minimal single-page chat UI
├── tests/
│   ├── __init__.py
│   ├── test_session.py
│   ├── test_dispatch.py
│   └── test_context.py
├── requirements.txt
└── README.md
```

---

## Related artifacts

- [ADR-002 — Model Gateway Pattern](0002-model-gateway-pattern.md) — all conductor model calls flow through this
- [ADR-003 — Knowledge Persistence Approach](0003-knowledge-persistence-approach.md) — session files follow this pattern
- [ADR-005 — Workflow Engine Technology](0005-workflow-engine-technology.md) — the runtime the conductor sits above
- [ADR-008 — Observation Store Architecture](0008-observation-store-architecture.md) — conductor turns become observations
- [ADR-010 — Runtime Model Evolution](0010-runtime-model-evolution.md) — the two-runtime model this extends to three
- [ADR-012 — Wyrd Subsystem Boundary](0012-wyrd-subsystem-boundary.md) — the identity context the conductor reads
- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — Layer 6c and Layer 8 updated
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-017 added
- [`docs/roadmap.md`](../docs/roadmap.md) — Phase 6 updated to include Conductor track
