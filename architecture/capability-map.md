# Capability Map

**ID:** DOC-005  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define the major capability domains of AIOS and map them to the target architecture layers. This document is the primary reference for scoping work, assigning traceability IDs, and evaluating where new capabilities belong.

Capability framing is preferred over premature agent-role framing. Capabilities describe what the system must be able to do; agent roles are a later runtime expression of how capabilities are delivered autonomously.

---

## Capability domains

### CAP-001 — Knowledge Management

**Purpose:** Create, store, retrieve, enrich, and lifecycle-manage canonical knowledge assets with full provenance.

**Primary layer:** Layer 4 — Knowledge Platform

**Capabilities:**
- Ingest documents and structured data into the knowledge store
- Assign and maintain provenance metadata (origin, date, author, version)
- Retrieve knowledge by identifier, metadata filter, or semantic query
- Version and archive knowledge assets
- Review and certify knowledge quality
- Separate canonical from derived knowledge
- Manage knowledge lifecycle (draft → active → review → deprecated → archived)
- Back up and restore the knowledge store

**Dependencies:** CAP-007 (Security/Policy), CAP-009 (Memory/Provenance)

---

### CAP-002 — Architecture Governance

**Purpose:** Maintain the living record of architectural decisions, principles, and standards; ensure traceability from intent to implementation.

**Primary layer:** Layer 5 — Architecture and Governance Repository

**Capabilities:**
- Author, review, and publish Architecture Decision Records
- Maintain architecture principles and standards
- Maintain and evolve the capability map
- Maintain the target architecture
- Assign and track traceability IDs
- Detect and flag broken traceability links
- Review architecture conformance against documented principles

**Dependencies:** CAP-007 (Traceability — see Governance below)

---

### CAP-003 — AI and Model Management

**Purpose:** Govern all AI model access through a single gateway; manage model selection, versioning, cost, safety, and audit.

**Primary layer:** Layer 3 — Model Gateway

**Capabilities:**
- Route model requests to appropriate providers
- Abstract model provider and version from calling components
- Enforce rate limits and cost budgets
- Log all model requests and responses for audit
- Apply prompt safety and output filtering policies
- Declare available model capabilities
- Support model evaluation and comparison

**Dependencies:** CAP-007 (Security/Policy), CAP-008 (Evaluation)

---

### CAP-004 — Workflow Orchestration

**Purpose:** Define, execute, audit, and govern bounded workflows; manage human approval gates and escalation.

**Primary layer:** Layer 6 — Workflow and Agent Runtime

**Capabilities:**
- Define workflow steps, triggers, and transitions
- Execute workflows in a governed, auditable runtime
- Integrate human approval gates at defined checkpoints
- Log full workflow execution traces
- Enforce circuit-breaker and escalation policies
- Associate workflow instances with capability IDs (traceability)
- Manage workflow scheduling and retry policies

**Dependencies:** CAP-003 (Model Management), CAP-007 (Security/Policy), CAP-001 (Knowledge)

---

### CAP-005 — Delivery Automation

**Purpose:** Integrate AIOS with software delivery workflows; automate governed delivery operations under traceability controls.

**Primary layer:** Layer 7 — Delivery and Automation Platform

**Capabilities:**
- Integrate with version control systems
- Trigger and monitor CI/CD pipelines
- Assist with code generation, review, and documentation (with human approval)
- Automate release and deployment operations (gated by autonomy stage)
- Capture delivery metrics and link to capability traceability

**Dependencies:** CAP-004 (Workflow Orchestration), CAP-007 (Security/Policy)

---

### CAP-006 — Observability

**Purpose:** Provide structured, retained visibility into platform state, decisions, actions, and outcomes across all layers.

**Primary layer:** Layer 1 (infrastructure); signals emitted by all layers

**Capabilities:**
- Collect and retain structured metrics, traces, and logs
- Provide operational dashboards for platform health
- Surface workflow execution status and history
- Surface AI model usage, cost, and quality signals
- Provide audit trail for all significant actions
- Support alerting and anomaly detection
- Define and enforce retention policies

**Dependencies:** All layers emit observability signals; this capability depends on no other capability but is consumed by all.

---

### CAP-007 — Security and Policy

**Purpose:** Enforce identity, access control, and policy evaluation across all platform operations; govern security events and credential lifecycle.

**Primary layer:** Layer 2 — Identity, Security, and Policy

**Capabilities:**
- Authenticate operators and platform components
- Evaluate access control policies at component boundaries
- Manage credentials and certificates
- Log and alert on security events
- Define and enforce least-privilege policies
- Support policy-as-code for governance rules
- Integrate with the human approval gate for policy-sensitive actions

**Dependencies:** Layer 1 (Platform Foundations)

---

### CAP-008 — Evaluation

**Purpose:** Assess the quality, correctness, and safety of AI outputs, knowledge assets, and automated workflows.

**Primary layer:** Layer 3 (model evaluation); Layer 4 (knowledge quality); Layer 6 (workflow outcomes)

**Capabilities:**
- Evaluate AI model output quality against defined criteria
- Score and certify knowledge asset quality
- Assess workflow execution outcomes against expected results
- Provide feedback loops for knowledge and model improvement
- Support human-in-the-loop evaluation workflows
- Maintain evaluation records for traceability

**Dependencies:** CAP-003, CAP-001, CAP-004

---

### CAP-009 — Memory and Provenance

**Purpose:** Maintain a persistent, queryable record of context, decisions, and actions that informs future reasoning and satisfies traceability requirements.

**Primary layer:** Layer 4 — Knowledge Platform; Layer 5 — Governance Repository

**Capabilities:**
- Record context from significant decisions and interactions
- Maintain provenance chains for knowledge assets and AI outputs
- Enable temporal queries over past decisions and actions
- Link memory records to the traceability hierarchy
- Govern retention and privacy of memory records

**Dependencies:** CAP-001, CAP-002

---

### CAP-010 — User and Operator Experience

**Purpose:** Provide effective, inspectable interfaces for operator interaction with all AIOS capabilities.

**Primary layer:** Layer 8 — Experience Layer

**Capabilities:**
- Knowledge management interface
- Workflow oversight and approval interface
- Observability and audit dashboards
- System configuration interface
- Conversational interaction surface (where appropriate)
- Notification and escalation delivery

**Dependencies:** All lower-layer capabilities; this is a consumer, not a producer.

---

## Capability-to-layer mapping

| Capability | Primary Layer |
|---|---|
| CAP-001 Knowledge Management | Layer 4 |
| CAP-002 Architecture Governance | Layer 5 |
| CAP-003 AI and Model Management | Layer 3 |
| CAP-004 Workflow Orchestration | Layer 6 |
| CAP-005 Delivery Automation | Layer 7 |
| CAP-006 Observability | Layer 1 (cross-cutting) |
| CAP-007 Security and Policy | Layer 2 |
| CAP-008 Evaluation | Layers 3, 4, 6 |
| CAP-009 Memory and Provenance | Layers 4, 5 |
| CAP-010 User and Operator Experience | Layer 8 |

## Related artifacts

- [`architecture/target-architecture.md`](target-architecture.md) — layers these capabilities map to
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — CAP-xxx ID convention
- [`docs/roadmap.md`](../docs/roadmap.md) — phases that deliver these capabilities
