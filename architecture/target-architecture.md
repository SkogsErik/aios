# Target Architecture

**ID:** DOC-004  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define the layered target architecture for AIOS. Each layer has a defined purpose, explicit responsibilities, non-responsibilities, and boundaries. This document governs how components are structured and how they interact.

## Architecture overview

AIOS is structured as eight vertical layers. Lower layers provide foundational capabilities consumed by higher layers. Each layer depends only on layers below it. Cross-layer dependencies require explicit documentation.

```
┌─────────────────────────────────────────────┐
│  8. Experience Layer                        │
├─────────────────────────────────────────────┤
│  7. Delivery and Automation Platform        │
├─────────────────────────────────────────────┤
│  6. Workflow and Agent Runtime              │
├─────────────────────────────────────────────┤
│  5. Architecture and Governance Repository  │
├─────────────────────────────────────────────┤
│  4. Knowledge Platform                      │
├─────────────────────────────────────────────┤
│  3. Model Gateway                           │
├─────────────────────────────────────────────┤
│  2. Identity, Security, and Policy          │
├─────────────────────────────────────────────┤
│  1. Platform Foundations                    │
└─────────────────────────────────────────────┘
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
- Service identity for platform components
- Access control policies (least-privilege by default)
- Policy evaluation at component boundaries
- Security event logging and alerting
- Certificate and credential lifecycle

**Non-responsibilities:**
- Knowledge storage
- Model calls
- Workflow execution

**Boundaries:**
- Every request from Layer 3 and above carries an identity context
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

**Non-responsibilities:**
- Generating knowledge (that is the responsibility of operators or governed workflows)
- Workflow execution
- Model inference

**Boundaries:**
- Canonical knowledge is version-controlled and never silently overwritten
- Derived artefacts are labelled and regenerable
- All access to this layer is authenticated and policy-governed (Layer 2)

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

**Purpose:** Provide the governed execution environment for defined, auditable workflows and agent roles.

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
- Delivery pipeline execution (delegated to Layer 7)

**Boundaries:**
- All workflow executions are bounded by a documented capability (Layer 5)
- Workflows that reach a human approval gate must pause until approval is received
- No workflow may bypass the model gateway (Layer 3) for model calls
- Autonomy stage governs which workflow types are permitted to run autonomously

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
- Operator interface for knowledge management, workflow oversight, and system configuration
- Conversational interaction surface (where appropriate, not the primary interface)
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
|---|---|---|
| Observability | Layer 1 (infrastructure); each layer emits signals | All layers emit structured metrics, traces, and logs |
| Security | Layer 2 (enforcement); each layer participates | Identity context flows through all layers |
| Traceability | Layer 5 (definition); applied by all layers | All components reference capability IDs |
| Backup/restore | Layer 1 (infrastructure); Layers 4 and 5 define policy | Knowledge and governance artefacts are backed up |

## Related artifacts

- [`architecture/principles.md`](principles.md) — principles that shaped this architecture
- [`architecture/capability-map.md`](capability-map.md) — capabilities mapped to layers
- [`governance/governance-model.md`](../governance/governance-model.md) — governance framework
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — autonomy constraints on Layer 6
