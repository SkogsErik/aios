# 0014 — Agent Tool Interface

**ID:** ADR-014
**Status:** Accepted (draft)
**Date:** 2026-06-12
**Affects:** CAP-017, CAP-018, THEME-004, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

ADR-013 (Conductor Agent Design) reserved the `execute` tool class for Phase 7+ and defined the Conductor as a conversational interface that routes operator intent to built-in tools (research, plan, summarise, converse). The `execute` class is the gateway to agent tool-use — the Conductor invoking specialised sub-agents (or tools) to perform concrete operations.

With Phase 6 and Phase 7 complete, the Conductor can classify intent, inject Wyrd context, and return model-generated responses. However, it cannot perform any action beyond generating text: it cannot read files, write output, run commands, or search the web on the operator's behalf. Every operator request that requires an action (not just a text response) has no path to execution.

The architecture now requires a **tool interface layer** that:

1. Defines a minimal, governed set of action primitives the Conductor can invoke
2. Binds those primitives to the existing dispatch mechanism so the `execute` intent class has a concrete target
3. Provides audit logging for every tool invocation (Principle 5 — Traceability, Principle 10 — Observability)
4. Enforces deterministic rules checks before any tool executes (ADR-009 two-layer model)
5. Supports operator confirmation gates (Principle 8 — Human approval for high-impact actions)
6. Follows the model gateway pattern — no tool may call a model directly (Principle 2)

---

## Decision

### Part 1: Tool interface protocol

Every tool is a class that implements a minimal protocol:

```python
class BaseTool(ABC):
    name: str                              # unique tool name, e.g. "read_file"
    description: str                        # human-readable description for model selection
    parameters: dict                        # JSON Schema for parameters

    @abstractmethod
    def run(self, **params) -> ToolResult:
        ...
```

Each tool invocation produces a `ToolResult`:

```python
@dataclass
class ToolResult:
    success: bool
    output: str                             # stdout / file content / search results
    error: str | None                       # error message on failure
    execution_time_ms: int
```

Tools are stateless. All state lives in the caller (the Conductor or an agent loop).

### Part 2: Four initial tools

| Tool | Parameters | What it does | Sandboxing |
|---|---|---|---|
| `read_file` | `path` (string) | Reads a file from the local filesystem | Path restricted to repo root or explicit allowlist; `../` traversal blocked |
| `write_file` | `path`, `content`, `mode` (overwrite/append) | Writes content to a file | Same path restriction; operator confirmation gate required |
| `run_shell` | `command` (string), `timeout` (int, default 30) | Runs a shell command and returns stdout/stderr | No interactive commands; timeout enforced; working directory restricted to repo root |
| `web_search` | `query` (string) | Searches the web via the configured web search provider | Read-only; no POST or authenticated requests |

### Part 3: Deterministic rules check (ADR-009)

Before any tool executes, a rules engine pass checks:

1. **Is this tool allowed in the current context?** (e.g. `write_file` requires operator confirmation; `run_shell` has a timeout cap)
2. **Are the parameters valid per the JSON Schema?** (reject malformed paths, dangerous shell patterns)
3. **Is there an active circuit-breaker for this tool?** (e.g. rate limit exceeded, too many failures)

If any check fails, the tool is not invoked and the failure is logged.

### Part 4: Operator confirmation gate

`write_file` requires explicit operator confirmation before execution. The gate is surfaced in the conversation: the Conductor asks "Write to path X? [y/N]" and waits for confirmation before invoking the tool.

Other tools (`read_file`, `run_shell` output-only, `web_search`) operate without operator confirmation at this stage — their impact is low-risk and reversible.

This matches the autonomy scope defined in ADR-013 Part 6:
- Research and summarise: fully autonomous
- Execute actions: require operator confirmation per impact level

### Part 5: Audit logging

Every tool invocation is logged as an observation with:
- `source_mechanism: "tool"`
- `source_component`: tool name
- Parameters (redacted of sensitive content)
- Result summary (truncated to 200 chars)
- Execution time
- Success/failure status

This feeds the existing observation pipeline and makes all tool actions traceable.

### Part 6: Hook into dispatch.py

The `execute` tool class (reserved in ADR-013) now routes to a `ToolExecutor` that:
1. Receives the classified intent and the operator's natural language request
2. The model determines which tool to call and with what parameters (from the tool descriptions and parameter schemas)
3. The executor validates the tool call against the rules check
4. If the tool requires confirmation, the Conductor asks the operator before executing
5. The executor runs the tool and returns the result
6. The result is handed back to the model for summarisation into a natural language response

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Minimal BaseTool protocol, four initial tools (this decision)** | Simple, testable, matches existing patterns; each tool is a single file | Limited capability set; no external API integration yet |
| **Rich plugin system with dynamic discovery** | Extensible without code changes | Premature abstraction (Principle 6); YAML-defined tools add complexity before four are proven |
| **Proxy all tools through a subprocess sandbox** | Stronger isolation | Big jump in complexity; runtime sandboxing is a Phase 8 concern; shell output-only is sufficient at this stage |
| **No tool layer — extend each existing tool to perform actions** | No new abstraction | Each tool (research, plan, summarise) would need bespoke action support; no uniform audit or rules enforcement |

---

## Rationale

The minimal protocol was chosen because:

- **It is consistent with existing tool structure.** The existing `tools/research.py`, `tools/plan.py`, etc. are thin wrappers. The new tools follow the same pattern but add a uniform result type and rules check.
- **It satisfies Principle 6 (simple foundations).** Four tools, a `@dataclass`, and a rules check is not over-engineering. A plugin system would be.
- **It is immediately useful.** With these four tools, the Conductor can read operator files, write output to new files, run diagnostic commands, and search the web for answers. This closes the gap between "text-only assistant" and "agent that can act."
- **It is auditable.** Every invocation is logged as an observation, which already has YAML persistence, date-based partitioning, and gateway integration.

---

## Consequences

**Positive:**
- The `execute` tool class (ADR-013) now has a concrete implementation target.
- Every tool invocation is audited through the existing observation pipeline.
- The rules check enforces ADR-009's two-layer model for tool execution.
- Write operations require operator confirmation, satisfying Principle 8.
- The four tools are directly testable with no model dependency.

**Negative:**
- `run_shell` is output-only with no interactive capability; some workflows require interaction (mitigated: interactive commands are deferred; output-only covers the vast majority of diagnostic/automation use cases).
- Path restrictions on `read_file`/`write_file` may frustrate operators who want to write outside the repo (mitigated: the allowlist is configurable; operator can update it).
- `web_search` relies on the web search provider configured in the gateway; if none is configured, the tool returns an error.

**Neutral:**
- Additional tools can be added by implementing the `BaseTool` protocol and registering in the registry — no ADR required for additional low-impact tools.
- Operator confirmation gates are conversational (the Conductor asks in the chat); the `execute` dispatch does not block — it surfaces the request.

---

## Directory structure changes

```
platform/conductor/
├── src/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseTool, ToolResult
│   │   ├── registry.py           # ToolRegistry, ToolExecutor
│   │   ├── read_file.py
│   │   ├── write_file.py
│   │   ├── run_shell.py
│   │   └── web_search.py        # (kept light; delegates to web search provider)
│   ├── tools/ (existing)
│   │   ├── research.py
│   │   ├── plan.py
│   │   ├── summarise.py
│   │   └── converse.py
│   ├── dispatch.py               # updated: execute tool class routes to ToolExecutor
│   └── ...
├── tests/
│   ├── test_tools_base.py
│   ├── test_tools_read_file.py
│   ├── test_tools_write_file.py
│   ├── test_tools_run_shell.py
│   ├── test_tools_web_search.py
│   └── test_tools_registry.py
```

---

## Related artifacts

- [ADR-002 — Model Gateway Pattern](0002-model-gateway-pattern.md) — all model calls go through the gateway, not tools
- [ADR-003 — Knowledge Persistence Approach](0003-knowledge-persistence-approach.md) — observation files follow this pattern
- [ADR-009 — Executive Reasoning Engine Pattern](0009-executive-reasoning-engine-pattern.md) — two-layer model (rules check before tool execution)
- [ADR-013 — Conductor Agent Design](0013-conductor-agent-design.md) — `execute` tool class reserved; autonomy scope defined
- [`architecture/principles.md`](../architecture/principles.md) — Principles 2, 4, 5, 6, 7, 8, 10 all relevant
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — Stage 1/2 autonomy for tool actions
