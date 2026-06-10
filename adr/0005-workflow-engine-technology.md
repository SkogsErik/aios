# 0005 — Workflow Engine Technology Selection

**ID:** ADR-005  
**Status:** Accepted  
**Date:** 2026-06-10  
**Affects:** CAP-004, THEME-004  
**Supersedes:** N/A  
**Superseded by:** N/A

---

## Context

Phase 4 requires a workflow runtime capable of executing bounded, inspectable, auditable workflows. The runtime must support:

- Workflow definitions that are human-readable and version-controlled
- Sequential step execution with logging at each step
- Human approval gates at defined checkpoints
- A full audit trail for every workflow execution
- Integration with the knowledge platform (CAP-001) and model gateway (CAP-003)
- Local-first operation with no external service dependencies at Phase 4 scale
- Simplicity sufficient to be proven correct before adding orchestration complexity

The platform is currently single-operator and local. Workflows at Phase 4 are primarily sequential pipelines (knowledge ingestion, model-assisted enrichment). Parallel execution, complex branching, and distributed scheduling are not required at this stage.

---

## Decision

Implement a **minimal custom Python workflow executor** with **YAML workflow definitions**.

Workflow definitions are YAML files stored in `workflows/`. The runtime (`platform/workflow-runtime/`) reads a YAML definition, resolves each step, executes steps sequentially, writes a structured audit log entry for each step, and enforces human approval gates where declared.

Steps are defined as shell commands. The runtime captures stdout/stderr for each step and records exit codes in the audit log.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Custom Python executor + YAML definitions (this decision)** | Fully local; no new dependencies; human-readable definitions; easy to audit; proven correct before adding complexity; consistent with existing Python+YAML approach | Limited to sequential execution at Phase 4; must implement error handling and approval gates manually |
| **Prefect** | Mature orchestration; Python-native; good observability | External service dependency (Prefect Cloud) or complex local setup; over-engineered for Phase 4 sequential workflows; heavy dependency |
| **Airflow** | Industry standard; rich scheduler | Server-based; database required; significant infrastructure overhead for a personal platform; violates "simply founded" principle |
| **Temporal** | Durable execution; strong consistency | Requires Temporal server; significant operational complexity; far beyond Phase 4 needs |
| **Makefile / shell scripts** | Zero new code | Not structured; no audit log; no approval gates; not machine-queryable; hard to govern |
| **n8n / Node-RED** | Visual editing; good integrations | Requires a running server; JavaScript ecosystem; inconsistent with Python platform |

---

## Rationale

The custom executor approach best satisfies AIOS design principles at Phase 4:

- **Simply founded.** A sequential executor with YAML definitions can be proven correct in a few hundred lines of Python. Complexity is added only when demonstrated need arises.
- **Local-first.** No external service, server, or database is required. The executor runs as a CLI command.
- **Traceable.** Each workflow definition carries a `WF-NNN` identifier and references the capability it implements. The audit log records every step execution with timestamp, exit code, and output.
- **Inspectable.** Workflow definitions are plain YAML, readable by any text editor. Audit logs are JSONL, queryable by any JSON tool.
- **Extensible.** When Phase 5 or 6 requires parallel execution, retries, or scheduling, the definitions format and audit schema are designed for forward compatibility. A migration to a more capable engine would preserve all existing definitions.

Prefect and Airflow were rejected because they introduce external service dependencies and significant operational overhead disproportionate to Phase 4 needs. Makefile/shell approaches were rejected because they produce no structured audit trail and cannot enforce governance controls.

---

## Consequences

**Positive:**
- Workflow definitions are version-controlled governance artefacts, consistent with the repository's architecture-first approach.
- Full audit trail for every execution without external infrastructure.
- Human approval gates are a first-class feature, not an afterthought.
- Zero new production dependencies beyond the standard library and PyYAML.

**Negative:**
- No built-in parallel execution, distributed scheduling, or failure recovery at Phase 4.
- Error handling and retry logic must be implemented manually if required.
- Approval gate implementation is basic (CLI prompt) at Phase 4; a richer approval interface requires a new ADR.

**Neutral:**
- Workflow definitions in `workflows/` are governance artefacts; changes follow the standard review process.
- Migration to a more capable engine in a later phase will require an ADR; existing definitions are designed to survive that transition.

---

## Risks

| Risk | Mitigation |
|---|---|
| Executor fails silently on step error | All step exit codes are checked; non-zero exit halts the workflow and records failure in audit log |
| Approval gate bypassed | Approval is required before execution resumes; approval decisions are logged with timestamp and operator ID |
| Workflow definition format evolves incompatibly | Definitions carry a `version` field; executor validates format version before execution |
| Complexity grows beyond what the simple executor can support | Phase 4 exit criteria are scoped to sequential workflows; migration to a capable engine requires a new ADR before Phase 5 escalates complexity |

---

## Related artifacts

- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-004 Workflow Orchestration
- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — Layer 6 Workflow and Agent Runtime
- [`governance/governance-model.md`](../governance/governance-model.md) — operational governance
- [`docs/roadmap.md`](../docs/roadmap.md) — Phase 4 deliverables and exit criteria
- [`adr/0006-model-gateway-technology.md`](0006-model-gateway-technology.md) — technology for the model gateway that workflows call
