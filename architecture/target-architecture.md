# Target Architecture

**ID:** DOC-004  
**Status:** Active  
**Last reviewed:** 2026-06-12

---

## Purpose

Define the layered target architecture for AIOS. Each layer has a defined purpose, explicit responsibilities, non-responsibilities, and boundaries. This document governs how components are structured and how they interact.

## Architecture overview

AIOS is structured as eight vertical layers. Lower layers provide foundational capabilities consumed by higher layers. Each layer depends only on layers below it. Cross-layer dependencies require explicit documentation.

```
┌─────────────────────────────────────────────────────────────┐
│  8. Experience Layer                                        │
│     (Web UI / Conductor interface / CLI / future channels)  │
├─────────────────────────────────────────────────────────────┤
│  7. Delivery and Automation Platform                        │
├──────────────────────────────────┬──────────────────────────┤
│  6c. Conductor                   │                          │
│  (interactive, operator-directed)│  6b. Executive Daemon    │
│                                  │  (continuous)            │
│                                  ├──────────────────────────┤
│                                  │  6a. Workflow Executor   │
│                                  │  (discrete, governed)    │
├──────────────────────────────────┴──────────────────────────┤
│  5. Architecture and Governance Repository                  │
├─────────────────────────────────────────────────────────────┤
│  4. Knowledge Platform (incl. Persona, Observation,         │
│     Project, Session stores) + Wyrd subsystem               │
├─────────────────────────────────────────────────────────────┤
│  3. Model Gateway                                           │
├─────────────────────────────────────────────────────────────┤
│  2. Identity, Security, and Policy                          │
│     (incl. Persona management)                              │
├─────────────────────────────────────────────────────────────┤
│  1. Platform Foundations                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Platform Foundations

**Purpose:** Provide the stable, local execution environment on which all other layers depend.

**Responsibilities:**
- Local compute, storage, and networking primitives
- Container or process isolation for platform components
- File system organisation and mount points
- Secrets management (local vault or equivalent)
- Platform-level observability: host metrics, disk, resource utilisation
- Backup and restore infrastructure for all persistent data

**Non-responsibilities:**
- Application logic
- Knowledge management
- Model inference

**Boundaries:**
- Consumed by Layer 2 and above
- Does not call into higher layers
- All persistent data stores are mounted and accessible from this layer

---

## Layer 2 — Identity, Security, and Policy

**Purpose:** Establish the identity context and policy evaluation framework for all platform operations.

**Responsibilities:**
- Operator identity and authentication
- Service identity for platform components (per ADR-004)
- **Persona (PRS) management**: the persistent representation of the operator — declared facts, preferences, values, beliefs, habits, constraints, relationships (per ADR-007)
- **Canonical/derived split**: operator-declared persona attributes are canonical; AI-inferred attributes are derived and require operator review before promotion
- Access control policies (least-privilege by default)
- Policy evaluation at component boundaries
- Security event logging and alerting
- Certificate and credential lifecycle

**Non-responsibilities:**
- Knowledge storage (except persona and observation stores, which are identity-adjacent)
- Model calls
- Workflow execution

**Boundaries:**
- Every request from Layer 3 and above carries an identity context
- Persona data is accessible to higher layers only through policy-governed interfaces
- Derived persona attributes are labelled as such and never mixed with canonical attributes
- Policy is evaluated at this layer before access to lower-layer resources is granted
- Security events are forwarded to the observability stack in Layer 1

---

## Layer 3 — Model Gateway

**Purpose:** Provide a single, governed, auditable interface to all AI models, abstracting provider, version, and modality.

**Responsibilities:**
- Routing model requests to appropriate providers (local or remote)
- Rate limiting, cost controls, and quota management
- Request and response logging for all model calls
- Model versioning and provider configuration
- Prompt safety and output filtering policies
- Capability declarations for available models

**Non-responsibilities:**
- Application-level prompt engineering (owned by calling layer)
- Knowledge retrieval (owned by Layer 4)
- Workflow orchestration (owned by Layer 6)

**Boundaries:**
- All model calls in all layers above flow through this gateway; no layer bypasses it
- Gateway configuration is a governance artifact, not application code
- No model-specific logic leaks above this layer

---

## Layer 4 — Knowledge Platform

**Purpose:** Provide the storage, retrieval, lifecycle, and provenance management for all canonical knowledge assets.

**Responsibilities:**
- Canonical knowledge storage (structured and unstructured)
- Provenance tracking: origin, creation date, version, authorship
- Metadata indexing and retrieval
- Lifecycle management: creation, review, deprecation, archival
- Separation of canonical from derived knowledge
- Embedding and semantic indexing of canonical assets (derived)
- Backup and versioning of the knowledge store
- **Persona store** (PRS persistence): declared and derived persona attributes, retention, export, deletion (per ADR-007)
- **Observation store**: automatic, manual, and scheduled observations with 90-day retention and lossy aggregation (per ADR-008)
- **Project and commitment stores**: lifecycle tracking for projects (PRJ), goals, focus areas, and commitments (per ADR-007 project context)

**Non-responsibilities:**
- Generating knowledge (that is the responsibility of operators or governed workflows)
- Workflow execution
- Model inference

**Boundaries:**
- Canonical knowledge is version-controlled and never silently overwritten
- Derived artefacts are labelled and regenerable
- All access to this layer is authenticated and policy-governed (Layer 2)
- Persona data follows the canonical/derived split (Principle 7)
- Observations are captured by Layer 6 triggers but stored in Layer 4

---

## Layer 5 — Architecture and Governance Repository

**Purpose:** Serve as the living record of all architectural decisions, governance artefacts, traceability links, and ontology definitions.

**Responsibilities:**
- Architecture Decision Records (ADRs)
- Architecture principles and standards
- Capability map and target architecture
- Governance model, autonomy maturity model, and traceability standard
- Ontology definitions
- Traceability chain from Vision to Implementation
- Roadmap and phase tracking

**Non-responsibilities:**
- Runtime platform logic
- Knowledge asset content (knowledge lives in Layer 4)
- Workflow definitions (workflows live in Layer 6)

**Boundaries:**
- This layer is primarily a documentation and governance artefact store, not a runtime component
- All documents are version-controlled in this repository
- Decisions made here govern layers above and below

---

## Layer 6 — Workflow and Agent Runtime

**Purpose:** Provide the governed execution environment for discrete, auditable workflows and agent roles (**CLI workflow executor**), and the continuous runtime for attention management, prioritization, and executive reasoning (**executive daemon**). These are two distinct runtimes that coexist via shared stores (per ADR-010).

### Sub-layer 6a — CLI Workflow Executor (governed discrete tasks)

**Responsibilities:**
- Workflow definition, scheduling, and execution
- Agent role instantiation within defined scope
- Workflow audit logging (full execution trace)
- Human approval gate integration
- Circuit-breaker and escalation policies
- Observability for workflow execution (duration, success, failure, approvals)

**Non-responsibilities:**
- Model inference (delegated to Layer 3)
- Knowledge persistence (delegated to Layer 4)
- Continuous executive functions (delegated to Sub-layer 6b)

**Boundaries:**
- All workflow executions are bounded by a documented capability (Layer 5)
- Workflows that reach a human approval gate must pause until approval is received
- No workflow may bypass the model gateway (Layer 3) for model calls
- Autonomy stage governs which workflow types are permitted to run autonomously

### Sub-layer 6c — Conductor (interactive, operator-directed)

**Purpose:** Provide the real-time conversational interface through which the operator directs the system in natural language. The conductor maintains session context, assembles Wyrd context for every model call, classifies operator intent, and routes to the appropriate tool. It is the interaction layer that makes all other subsystems immediately useful.

**Responsibilities:**
- Receive operator messages through the local web interface
- Manage conversation sessions: history, context snapshots, persistence
- Assemble context from Wyrd stores (persona, active projects, recent observations) for every model call
- Classify operator intent and route to: research, plan, summarise, or converse tools
- Call the model gateway (Layer 3) for all AI inference
- Persist session turns as observations (feeding Wyrd's observation stream)
- Delegate to governed workflows (Sub-layer 6a) for well-defined subtasks, with operator confirmation

**Non-responsibilities:**
- Does not manage attention state (delegated to Sub-layer 6b)
- Does not execute governed workflows autonomously — requires operator confirmation
- Does not modify canonical persona or project data (operator uses CLI)
- Does not spawn autonomous sub-agents

**Boundaries:**
- The conductor is optional — the system operates without it (minus interactive capability)
- All model calls flow through the model gateway; the conductor never calls models directly
- Session persistence follows ADR-003 (file-based YAML at `platform/knowledge/sessions/`)
- Binds to `localhost` only; single-operator, no authentication

---

### Sub-layer 6b — Executive Daemon (continuous executive function + scheduled learning)

**Responsibilities:**
- Persistent event loop: monitors time triggers, state changes, and external events
- Attention manager: tracks active/dormant/forgotten/resurfaced states with decay functions
- Rules engine (Layer 1, deterministic): stall detection, deadline scoring, fragmentation alerts, dependency traversal, unblocking notifications (per ADR-009)
- Priority computation: deterministic scoring (urgency × commitment_weight × momentum)
- Reflection engine: schedules and orchestrates daily/weekly/monthly/quarterly reflection cycles
- **Learning engine** (Layer 2, scheduled, model-dependent): pattern detection, preference reconciliation, confidence scoring, candidate generation, prediction evaluation (per ADR-011)
- Trigger evaluation: evaluates rules engine triggers and produces operator notifications
- State checkpointing: periodic serialization of attention state, priority rankings, and daemon state

**Non-responsibilities:**
- Executing governed workflows (delegated to Sub-layer 6a)
- Making model calls (delegated to Layer 3; AI reasoning in Layer 2 is optional and scheduled)
- Modifying persona attributes (all executive inferences are derived; operator approval required for promotion)

**Boundaries:**
- The executive daemon is optional; the system operates without it at reduced capability (no proactive alerts, no attention management, no reflection scheduling)
- The daemon does not require AI model availability for any Layer 1 (deterministic) operation
- **Layer 2 (AI reasoning / learning engine)** is scheduled separately and requires model gateway access; it degrades gracefully when unavailable — patterns are simply not updated
- State is persisted to shared stores in Layer 4; daemon restart restores from last checkpoint
- All executive daemon outputs are visible to the operator for review and override
- **All learning engine outputs are derived** (Principle 7) and require operator review before influencing the persona

---

## Layer 7 — Delivery and Automation Platform

**Purpose:** Integrate AIOS with software delivery and operational automation workflows.

**Responsibilities:**
- CI/CD pipeline integration
- Code generation, review, and merge automation (under governance)
- Release and deployment automation
- Integration with version control systems
- Delivery metrics and traceability to capabilities

**Non-responsibilities:**
- Core knowledge management (delegated to Layer 4)
- General workflow orchestration (delegated to Layer 6)
- Model management (delegated to Layer 3)

**Boundaries:**
- All delivery automation is governed by the same traceability and approval standards as other workflows
- Delivery actions with production impact require human approval until the autonomy maturity model permits automation
- Delivery metrics feed the observability stack

---

## Layer 8 — Experience Layer

**Purpose:** Provide the operator-facing interfaces for interacting with AIOS across all capability domains.

**Responsibilities:**
- Conductor web interface: primary real-time interaction surface (served by Sub-layer 6c)
- Operator interface for knowledge management, workflow oversight, and system configuration
- Conversational interaction surface (conductor provides this)
- Approval and review interfaces for AI-suggested actions
- Observability and audit dashboards
- Notification and escalation delivery

**Non-responsibilities:**
- Core logic of any lower layer
- Knowledge storage
- Workflow execution

**Boundaries:**
- All actions initiated from this layer flow through identity and policy enforcement (Layer 2)
- This layer is a consumer, not an owner, of all lower-layer capabilities
- Conversational interfaces must not bypass governance controls

---

## Cross-cutting concerns

The following concerns apply across all layers:

| Concern | Layer ownership | Notes |
|---|---|---|---|
| Observability | Layer 1 (infrastructure); each layer emits signals | All layers emit structured metrics, traces, and logs |
| Security | Layer 2 (enforcement); each layer participates | Identity context flows through all layers |
| Traceability | Layer 5 (definition); applied by all layers | All components reference capability IDs |
| Backup/restore | Layer 1 (infrastructure); Layers 4 and 5 define policy | Knowledge and governance artefacts are backed up |
| Executive context | Layer 2 (persona), Layer 4 (stores), Layer 6b (daemon) | Persona, attention, priorities, decisions, and inferred patterns form the executive context available to higher layers |
| Learning & inference | Layer 6b (learning engine), Layer 4 (pattern stores) | Inferred patterns, contradictions, and predictions are derived assets managed through feedback loops |
| Interactive assistance | Layer 6c (conductor), Layer 8 (web UI) | Operator-directed tasks, sessions, context-injected model calls; session turns flow back to Layer 4 as observations |

## Related artifacts

- [`architecture/principles.md`](principles.md) — principles that shaped this architecture
- [`architecture/capability-map.md`](capability-map.md) — capabilities mapped to layers
- [`governance/governance-model.md`](../governance/governance-model.md) — governance framework
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — autonomy constraints on Layer 6
- [ADR-007 — Identity as Domain Object](../adr/0007-identity-as-domain-object.md) — Layer 2 persona model update
- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md) — Layer 4 observation store addition
- [ADR-009 — Executive Reasoning Engine Pattern](../adr/0009-executive-reasoning-engine-pattern.md) — Layer 6b rules engine + AI reasoning design
- [ADR-010 — Runtime Model Evolution](../adr/0010-runtime-model-evolution.md) — Layer 6 two-runtime model (extended to three by ADR-013)
- [ADR-011 — Learning Architecture](../adr/0011-learning-architecture.md) — Layer 6b learning engine design
- [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md) — Layer 4 Wyrd domain split
- [ADR-013 — Conductor Agent Design](../adr/0013-conductor-agent-design.md) — Layer 6c conductor design
