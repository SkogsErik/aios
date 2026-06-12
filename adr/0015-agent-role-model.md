# 0015 — Agent Role Model

**ID:** ADR-015
**Status:** Accepted (draft)
**Date:** 2026-06-12
**Affects:** CAP-017, CAP-018, THEME-004, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

ADR-014 introduced the tool interface layer — four action primitives (`read_file`, `write_file`, `run_shell`, `web_search`) that the Conductor can invoke. Tools are stateless, untyped, and have no capability boundaries beyond the rules check and operator confirmation gate.

As the Conductor evolves toward multi-agent orchestration (Phase 8), it needs a way to model agent roles — bounded capability sets that constrain what a given agent type can do. Without role definitions, any agent can call any tool, which violates Principle 4 (governance before autonomy) and Principle 8 (human approval for high-impact actions).

Three immediate role types are needed:

1. **Researcher** — gathers information (web search, file reads); may not write or execute
2. **Coder** — reads, writes, and runs shell commands within a sandbox; may not search the web
3. **Synthesizer** — reads and produces structured output; may not write to canonical state or run commands

Each role maps to a distinct task profile in the operator's workflow. Defining them explicitly enables governance (what can each role do?), audit (which role performed this action?), and eventual orchestration (which role should handle this sub-task?).

---

## Decision

### Part 1: Role definition format

Agent roles are defined as YAML files in `platform/conductor/agents/`. Each file contains:

```yaml
# agents/researcher.yaml
role: researcher
description: Gathers information from files and the web. Read-only.
allowed_tools:
  - read_file
  - web_search
forbidden_actions:
  - write_file
  - run_shell
context_access:
  - persona
  - projects
  - goals
escalation_triggers:
  - action: Operator requested write or shell execution
    response: Inform operator that researcher role cannot perform this action; suggest coder role
```

The YAML format is:
- **role**: unique role name (snake_case)
- **description**: human-readable explanation of the role's purpose
- **allowed_tools**: list of tool names this role may call
- **forbidden_actions**: list of tool names this role may not call (double-containment with allowed_tools)
- **context_access**: which Wyrd context sections the role can read (persona, projects, goals, focus)
- **escalation_triggers**: conditions under which the role escalates to the operator or a different role

### Part 2: Three initial roles

| Role | Allowed tools | Forbidden | Context access | Escalation |
|---|---|---|---|---|
| **researcher** | read_file, web_search | write_file, run_shell | persona, projects, goals | If operator asks researcher to write or execute, suggest coder role |
| **coder** | read_file, write_file, run_shell | web_search | persona, projects, goals, focus | If operator asks coder to search web, suggest researcher role |
| **synthesizer** | read_file | write_file, run_shell, web_search | persona, projects, goals | If operator asks synthesizer to act, inform that synthesizer produces structured output only |

### Part 3: Role enforcement

The `ToolExecutor` (ADR-014) is extended to accept an optional `role` parameter. When a role is provided:

1. Before executing any tool, the executor checks that the tool is in the role's `allowed_tools` list.
2. If the tool is not allowed, the executor returns a denial with a reference to the escalation trigger.
3. The audit log records the role name alongside the tool invocation.

When no role is provided, the Conductor operates at the default assistant capability (all tools, with operator confirmation for `write_file`).

### Part 4: Role loading

Roles are loaded from `platform/conductor/agents/*.yaml` at startup. The `RoleRegistry` provides:
- `get(role_name)` → role dict
- `list_roles()` → all defined roles
- `validate_tool_access(role_name, tool_name)` → bool + optional escalation message

### Part 5: No autonomous role assignment

At this stage, roles are assigned explicitly by the operator or by the Conductor's task loop (Step 2+). There is no autonomous role-switching. This is consistent with Autonomy Stage 2 (assisted, with operator review).

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **YAML-defined roles with tool allowlists (this decision)** | Governable, inspectable, follows ADR-003 pattern; easy to add/modify roles | YAML files must be kept in sync with tool registry; no dynamic role creation |
| **Hardcoded role classes in Python** | Compile-time safety; no parsing errors | Changing roles requires code changes and redeployment; violates Principle 6 (simple foundations before complex orchestration) — YAML is simpler |
| **No roles — all tools available to all agents** | Simplest to implement | No governance; any agent can do anything; violates Principle 4 |
| **Role-based access control (RBAC) with inheritance** | More flexible for complex hierarchies | Premature abstraction; three roles don't need inheritance; can be added later |

---

## Rationale

YAML-defined role files were chosen because:

- **Inspectable and version-controlled.** Role definitions are governance artefacts, not code. An operator can review, modify, or add roles without touching Python source.
- **Consistent with ADR-003.** The YAML-based persistence approach already governs knowledge assets, workflows, and sessions. Role definitions extend the same pattern to agent capabilities.
- **Tool allowlists are explicit and auditable.** Each role's file is a single source of truth for what that role may do. There is no ambiguity about capability boundaries.
- **Escalation triggers document the governance boundary.** They tell both the operator and the system what to do when a role is asked to exceed its capability.
- **Double-containment (allowed + forbidden) prevents accidents.** If a tool is added but not listed in allowed_tools, it is implicitly denied. If it's listed in both allowed and forbidden, forbidden wins.

---

## Consequences

**Positive:**
- Agent actions are governed by explicit, inspectable role definitions.
- The audit log records which role performed each action.
- New roles can be added by creating a YAML file — no code change required.
- The ToolExecutor enforces role boundaries at the governance layer (before execution).

**Negative:**
- Role definitions must be kept in sync with the tool registry. Adding a new tool requires reviewing all role definitions.
- YAML parsing errors could disable role enforcement (mitigated: startup validation and test coverage).

**Neutral:**
- Role assignment is manual at this stage. Autonomous role assignment is deferred to Phase 8 (multi-agent orchestration).
- The three initial roles are intentionally separated by capability. A combined "full-access" role is not defined yet — it will be defined in a future ADR when autonomous operation requires it.

---

## Directory structure

```
platform/conductor/
├── agents/
│   ├── researcher.yaml
│   ├── coder.yaml
│   └── synthesizer.yaml
├── src/
│   ├── agents.py               # RoleRegistry, load_roles, validate_tool_access
│   ├── tools/
│   │   ├── registry.py          # updated: execute() accepts optional role
│   │   └── ...
│   └── ...
```

---

## Related artifacts

- [ADR-003 — Knowledge Persistence Approach](0003-knowledge-persistence-approach.md) — YAML-based persistence pattern
- [ADR-014 — Agent Tool Interface](0014-agent-tool-interface.md) — tool interface this role model governs
- [`architecture/principles.md`](../architecture/principles.md) — Principle 4 (governance before autonomy), Principle 8 (human approval)
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — Stage 1/2 governance requirements
