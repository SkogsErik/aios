# 0010 — Runtime Model Evolution

**ID:** ADR-010
**Status:** Accepted
**Date:** 2026-06-10
**Affects:** CAP-004, CAP-009, THEME-004, THEME-006
**Supersedes:** ADR-005 (partial)
**Superseded by:** N/A

---

## Context

ADR-005 established a CLI-invoked workflow executor as the runtime model for AIOS. Workflows are defined as YAML files, executed by `python src/cli.py run <definition> --var key=value`, and produce a structured audit log. This was the correct decision for Phase 4: sequential, bounded, governed tasks invoked explicitly by the operator.

The executive cognition architecture (DOC-017) requires a fundamentally different runtime model:

- **Continuous operation.** The attention manager and rules engine (ADR-009) must run on a trigger cycle, not on operator invocation. Stall detection is useless if it only runs when the operator remembers to call it.

- **Persistent state.** Attention state (active/dormant/forgotten), decay values, and trigger conditions must survive process restarts. A CLI that loads state fresh on every invocation cannot support this.

- **Event-driven triggers.** The system must respond to calendar events, file system changes, git activity, and time-based schedules — not just operator commands.

- **Cross-store queries.** The executive reasoning engine reads from projects, commitments, observations, goals, risks, and persona simultaneously. This requires shared state accessible across invocations.

However, the existing CLI workflow executor is not wrong for its purpose. Governed, auditable, bounded workflows remain the correct execution model for discrete tasks like knowledge ingestion, model queries, and delivery operations.

**The solution is not to replace ADR-005. It is to introduce a second runtime that coexists with it.**

---

## Decision

### Part 1: Two-runtime architecture

AIOS operates two runtimes that coexist and share infrastructure:

```
┌──────────────────────────────────────────────────────────────┐
│  RUNTIME A: Workflow Executor (preserved from ADR-005)       │
│                                                               │
│  Purpose: Execute governed, bounded, discrete workflows      │
│  Process model: CLI invocation → execute → exit              │
│  State: Loaded per invocation from YAML definition            │
│  Triggers: Operator command                                   │
│  Audit: Per-execution JSONL record                            │
│  Examples: knowledge ingest, model query, delivery task       │
│                                                               │
│  Location: platform/workflow-runtime/ (unchanged)             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  RUNTIME B: Executive Daemon (new)                            │
│                                                               │
│  Purpose: Continuous executive function (attention, rules,    │
│           scheduling, reflection triggers)                    │
│  Process model: Persistent daemon with event loop             │
│  State: Persistent in-memory state backed by file store        │
│  Triggers: Time-based, event-based, pattern-based             │
│  State persistence: Attention state, decay values, queues     │
│  Examples: attention manager, rules engine, reflection        │
│            scheduler, observation capture daemon              │
│                                                               │
│  Location: platform/executive-daemon/ (new)                   │
└──────────────────────────────────────────────────────────────┘

Shared across both:
├── Model gateway (platform/model-gateway/)
├── Knowledge store (platform/knowledge/store/)
├── Observation store (platform/knowledge/observations/)
├── Project store (platform/knowledge/projects/)
├── Persona store (platform/knowledge/persona/)
└── Model gateway audit log (platform/model-gateway/audit/)
```

### Part 2: Executive daemon design

The executive daemon is a lightweight Python process with the following components:

```
platform/executive-daemon/
├── src/
│   ├── main.py              # Entry point, event loop, lifecycle
│   ├── rules_engine.py      # Layer 1: deterministic rules (ADR-009)
│   ├── attention_manager.py # Attention state, decay, triggers
│   ├── scheduler.py         # Time-based and event-based triggers
│   ├── reflection_orch.py   # Reflection cycle orchestration
│   ├── observation_capture.py # Passive capture hooks
│   └── cli.py               # start, stop, status commands
├── state/
│   ├── attention_state.yaml  # Persistent attention state
│   └── trigger_queue.yaml    # Pending trigger events
├── requirements.txt
└── README.md
```

**Lifecycle:**
- `python src/cli.py start` — launches daemon in background
- `python src/cli.py stop` — saves state, terminates cleanly
- `python src/cli.py status` — reports running, idle, or stopped
- State is saved to YAML on stop and restored on start
- Crash recovery: state is checkpointed every 5 minutes

**Event loop:**
```
while running:
    # Phase 1: Trigger evaluation
    for trigger in active_triggers:
        if trigger.condition_met():
            trigger.fire()
    
    # Phase 2: Rules engine pass (ADR-009 Layer 1)
    rules_engine.run()
    
    # Phase 3: Attention decay computation
    attention_manager.compute_decay()
    
    # Phase 4: State checkpoint (every 5 minutes)
    if minutes_since_last_checkpoint >= 5:
        state.save()
    
    sleep(configurable_interval, default=60s)
```

**Triggers the daemon evaluates:**
- Time-based: scheduled reflection cycles (daily at X, weekly on Y)
- Deadline-based: commitments within threshold
- Stall-based: projects without attention for N days
- Dependency-based: blocked projects whose blockers have resolved

### Part 3: Coexistence rules

1. The workflow executor and executive daemon are independent processes. They do not call each other directly.
2. Both read from and write to the same shared stores (observations, projects, commitments).
3. The executive daemon may trigger workflow execution by writing a trigger file that the workflow CLI can pick up, but does not execute workflows itself.
4. The workflow executor continues to function exactly as before when invoked directly by the operator.
5. The executive daemon is optional — the system operates without it (minus executive functions).

### Part 4: What is superseded from ADR-005

This ADR supersedes the following constraints from ADR-005:

| ADR-005 constraint | Status | Rationale |
|---|---|---|
| "The runtime runs as a CLI command" | Superseded for executive daemon | Executive functions require continuous operation |
| "No server, no daemon" | Superseded for executive daemon | Required for trigger-based, time-based operations |
| "State loaded per invocation" | Superseded for executive daemon | Attention state and decay require persistence |

The following from ADR-005 are **not** superseded and remain in effect:

| ADR-005 decision | Status | Rationale |
|---|---|---|
| YAML-based workflow definitions | Preserved | Still correct for governed workflows |
| Subprocess execution per step | Preserved | Still correct for discrete tasks |
| JSONL audit logging | Preserved | Still correct for workflow audit |
| Human approval gates | Preserved | Still required for governed workflows |
| Minimal custom executor | Preserved | Proven correct; no reason to replace |

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Two-runtime architecture (this decision)** | Preserves ADR-005 investment; clear separation of concerns; executive daemon can be built independently; no regression risk for existing workflows | Two process models to maintain; state synchronization between runtimes |
| **Extend workflow executor to support daemon mode** | Single codebase; shared patterns | ADR-005 executor was designed for CLI invocation; adding daemon mode would compromise its simplicity; risk of regression in workflow executor |
| **Single monolithic daemon** | One process to manage | Conflates governed discrete tasks with continuous executive functions; different failure modes, different governance |
| **Replace workflow executor with new runtime** | Clean slate | Discards working, tested, audited code; unnecessary disruption; ADR-005 executor is correct for its domain |

---

## Rationale

The two-runtime approach was chosen because:

- **Preserves existing investment.** The workflow executor (ADR-005) is working, tested, and correct for governed discrete tasks. Replacing it provides no benefit and introduces regression risk.

- **Different failure modes.** A daemon crash should not affect the ability to execute governed workflows. A workflow bug should not crash the daemon. Separate processes isolate failure domains.

- **Different governance.** Workflow execution requires audit trails, approval gates, and capability traceability. Executive function requires attention state management, decay computation, and trigger evaluation. These have different governance requirements (see ADR-009).

- **Independent evolution.** The executive daemon can be built, tested, and deployed without modifying the workflow executor. The workflow executor continues to function exactly as before.

- **Graceful degradation.** The system operates without the daemon — it simply lacks executive functions (attention management, proactive alerts, reflection cycles). This is consistent with the "simply founded" principle.

---

## Consequences

**Positive:**
- Executive functions operate continuously without requiring operator invocation.
- The existing workflow executor is untouched and continues to function for governed discrete tasks.
- State persistence enables attention decay tracking across sessions.
- Event-driven triggers enable proactive behavior (stall alerts, deadline warnings).
- The daemon is optional — the system works without it at reduced capability.

**Negative:**
- A second runtime to build, test, and maintain.
- State checkpointing adds complexity and potential failure mode.
- Two runtimes sharing stores must coordinate to avoid conflicts (file-level locking or convention).
- Daemon lifecycle management (start, stop, restart, crash recovery) adds operational overhead.

**Neutral:**
- The daemon is local-only (no network service). It does not change the local-first architecture.
- The daemon requires no external dependencies beyond the Python standard library.
- The daemon shares the model gateway and stores with the workflow executor — no data duplication.

---

## Risks

| Risk | Mitigation |
|---|---|
| Daemon crashes without clean state save | Periodic checkpointing (5-minute intervals); state is recoverable from store data |
| Daemon and workflow executor write to same store simultaneously | File-level locking or append-only conventions; stores are designed for single-writer at Phase 5 scale |
| Daemon consumes resources continuously | Configurable sleep interval; idle mode when operator is inactive (detected from observation patterns) |
| Daemon introduces security surface | No network service; local Unix socket only if needed; follows ADR-004 service identity model |
| Operator forgets daemon is running | Status CLI command; visual indicator in experience layer (future) |

---

## Related artifacts

- [ADR-005 — Workflow Engine Technology Selection](0005-workflow-engine-technology.md) — partially superseded by this ADR
- [ADR-009 — Executive Reasoning Engine Pattern](0009-executive-reasoning-engine-pattern.md) — defines the rules engine that the daemon runs
- [DOC-017 — Executive Cognition Analysis](../architecture/executive-cognition-analysis.md) — analysis requiring continuous operation
- [DOC-018 — Pivot Readiness Assessment](../architecture/pivot-readiness-assessment.md) — peer review that identified the implementation gap
- [Architecture Principle 6 — Simple Foundations](../architecture/principles.md) — daemon starts simple, complexity added only when demonstrated necessary
