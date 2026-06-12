# 0016 — Orchestration Pattern

**ID:** ADR-016
**Status:** Accepted (draft)
**Date:** 2026-06-12
**Affects:** CAP-017, CAP-018, THEME-004, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

ADR-013 (Conductor Agent Design) defined the Conductor as Runtime C — an interactive conversational interface. ADR-014 introduced a governed tool interface with four action primitives. ADR-015 defined agent roles (researcher, coder, synthesizer) with explicit capability boundaries. The ReactRunner (implementation of Step 2) provides a single-agent ReAct loop that pursues a goal through repeated reasoning and tool use.

What is missing is **orchestration** — the ability to decompose a complex, multi-part goal into sub-tasks and route each to the appropriate agent role, then combine results into a coherent outcome. Without orchestration, each goal requires either a single monolithic ReAct loop (which conflates multiple concerns) or manual operator decomposition into separate tasks.

The operator's natural workflow is not single-step: "Research the topic, write the code, test it, and produce a summary" is a four-part goal that benefits from different roles (researcher gathers information, coder implements, synthesizer produces structured output). A single ReAct loop with a single role cannot efficiently switch between information gathering, implementation, and synthesis.

---

## Decision

### Part 1: The orchestration pattern

A **plan** is a sequence of steps, each of which is a goal + role pair. The orchestrator:

1. **Decomposes** the operator's goal into a plan (list of steps with roles)
2. **Validates** the plan through operator review
3. **Executes** each step sequentially via the existing ReactRunner + TaskStore
4. **Accumulates** results from each step as context for the next
5. **Presents** the final outcome to the operator

```
Operator goal → Model decomposition → Plan (steps with roles)
                                       ↓
                              Operator review/approval
                                       ↓
                        ┌──────────────────────────┐
                        │  Step 1: researcher       │
                        │  → ReactRunner.run(goal)  │
                        │  → result stored          │
                        │  → context for next step  │
                        ├──────────────────────────┤
                        │  Step 2: coder            │
                        │  → ReactRunner.run(goal)  │
                        │  → result stored          │
                        │  → context for next step  │
                        ├──────────────────────────┤
                        │  Step N: ...              │
                        └──────────────────────────┘
                                       ↓
                              Final outcome presented
```

### Part 2: Plan data model

A plan has:
- **id**: `PLN-YYYY-MMDD-NNN`
- **goal**: the operator's original request
- **steps**: ordered list of step dicts

Each step has:
- **id**: `STP-NNN` (within the plan)
- **goal**: what this step should accomplish
- **role**: which agent role handles it (researcher, coder, or synthesizer)
- **status**: pending → in_progress → completed / failed / blocked
- **task_id**: reference to the TaskStore entry (TSK-NNN)
- **result**: the output from the step execution
- **error**: error message if failed

### Part 3: Decomposition via model call

The decomposition is performed by the model gateway. A single model call with a decomposition prompt analyses the operator's goal and produces a structured plan:

```
Goal: "Build a Python script that scrapes docs and produces a summary"

Proposed plan:
  Step 1 (researcher): Research web scraping libraries for Python
  Step 2 (researcher): Find documentation structure for the target site
  Step 3 (coder): Write the scraping script
  Step 4 (coder): Test the script
  Step 5 (synthesizer): Generate documentation summary from output
```

The operator reviews and can approve, modify, or reject the plan before execution.

### Part 4: Sequential execution

At Phase 8 entry, steps execute **sequentially**. Each step's result is appended to a shared context block that feeds into the next step's ReAct loop. This ensures later steps can reference earlier findings.

Parallel execution is deferred — it requires dependency resolution and merge logic that are not yet justified.

### Part 5: Error handling

If a step fails:
1. The orchestrator records the error in the step record
2. It pauses and surfaces the error to the operator
3. The operator may: retry the step (possibly with different instructions), skip the step, modify the remaining plan, or cancel the entire plan
4. If the operator does not respond within a defined period, the plan enters a `blocked` state

### Part 6: Relationship to existing components

| Component | Role in orchestration |
|---|---|
| `ReactRunner` | Executes each step's ReAct loop |
| `TaskStore` | Persists each step as a task (TSK-NNN) |
| `RoleRegistry` | Enforces tool access for each step's assigned role |
| `ToolExecutor` | Governs individual tool calls within each step |
| `Conductor.chat()` | Entry point for the operator to approve/modify plans |
| `PlanOrchestrator` | New — decomposes, tracks, and coordinates steps |

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Sequential orchestration with operator review (this decision)** | Simple, auditable, human-in-the-loop; reuses all existing components | Slower than parallel; operator must review each plan |
| **Parallel execution with dependency graph** | Faster for independent sub-tasks | Complex dependency resolution; merge logic; no demonstrated need yet; harder to audit |
| **Single monolithic ReAct loop (no orchestration)** | No new component needed | Cannot switch roles mid-task; context grows unbounded; tool access is uniform across all steps |
| **Operator must manually decompose goals** | Simplest to build | Highest operator burden; defeats the purpose of orchestration |

---

## Rationale

Sequential orchestration was chosen because:

- **It reuses the existing task infrastructure.** Each step is a standard task (TSK-NNN) created via the existing `Conductor.run_task()`. No new persistence mechanism is needed.
- **It preserves human oversight.** The operator reviews the plan before any execution and can intervene after any step failure.
- **It is auditable.** Each step's full tool call history, observations, and outcome are recorded in the TaskStore.
- **It is simple.** No dependency graph, no parallel merging, no inter-agent communication protocol.
- **It does not foreclose parallel execution.** A future iteration can add a dependency field to steps and a parallel scheduler — the data model supports it.

---

## Consequences

**Positive:**
- Multi-part goals can be decomposed and executed with appropriate role assignment per step.
- Each step is independently tested, logged, and recoverable.
- The operator reviews the plan before execution — no autonomous multi-step execution at this stage.
- The orchestrator is a thin coordination layer — most logic lives in existing components.

**Negative:**
- Sequential execution is slower than parallel for independent sub-tasks.
- The decomposition model call adds latency before the first step executes.
- Operator review of each plan can feel like friction for experienced operators.

**Neutral:**
- Plans are derived state (ADR-014 Principle 7). They are not canonical and do not modify Wyrd stores.
- The orchestrator does not introduce new agent roles — it routes to the three defined roles (researcher, coder, synthesizer).

---

## Directory structure changes

```
platform/conductor/src/
├── orchestrator.py              # PlanOrchestrator — new
└── conductor.py                 # updated: create_plan, execute_plan, get_plan methods
```

---

## Related artifacts

- [ADR-013 — Conductor Agent Design](0013-conductor-agent-design.md) — Runtime C definition
- [ADR-014 — Agent Tool Interface](0014-agent-tool-interface.md) — tools that steps use
- [ADR-015 — Agent Role Model](0015-agent-role-model.md) — roles that steps are assigned to
- [`architecture/principles.md`](../architecture/principles.md) — Principle 4 (governance before autonomy), Principle 8 (human approval)
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — Stage 2 (assisted, with operator review)
