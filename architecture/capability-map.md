# Capability Map

**ID:** DOC-005  
**Status:** Active  
**Last reviewed:** 2026-06-11

---

## Purpose

Define the major capability domains of AIOS and map them to the target architecture layers. This document is the primary reference for scoping work, assigning traceability IDs, and evaluating where new capabilities belong.

Capability framing is preferred over premature agent-role framing. Capabilities describe what the system must be able to do; agent roles are a later runtime expression of how capabilities are delivered autonomously.

Capabilities are grouped into two implementation domains:

- **AIOS core** (`platform/executive-daemon/`, `platform/knowledge/`, `platform/model-gateway/`, `platform/workflow-runtime/`) — inference engines, daemon lifecycle, model gateway, workflow runtime
- **Wyrd** (`wyrd/`) — operator understanding: persona, observations, projects, commitments, goals, capture sources, review interface. See [ADR-012](../adr/0012-wyrd-subsystem-boundary.md).
- **Conductor** (`platform/conductor/`) — interactive operator interface: conversational dispatch, session management, tool routing. See [ADR-013](../adr/0013-conductor-agent-design.md).

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

### CAP-011 — Identity and Persona Management *(Wyrd domain)*

**Purpose:** Maintain the persistent representation of the operator, including declared facts, preferences, values, and the canonical/derived split for persona attributes.

**Primary layer:** Layer 4 — Knowledge Platform; Layer 2 — Identity, Security, and Policy

**Capabilities:**
- Create, update, and version the Persona (PRS) entity
- Manage declared facts (values, beliefs, preferences, habits, constraints)
- Manage inferred attributes (AI-detected patterns, awaiting operator review)
- Promote inferred attributes to declared facts only after operator approval
- Export and delete all persona data
- Provide persona context to all layers above Layer 2

**Dependencies:** CAP-001 (Knowledge Management), CAP-007 (Security/Policy)

---

### CAP-012 — Observation and Capture *(Wyrd domain)*

**Purpose:** Capture, deduplicate, store, and retain observations from automatic, manual, and scheduled sources. Observations are the raw material for all executive reasoning and reflection.

**Primary layer:** Layer 4 — Knowledge Platform; Layer 6 — Workflow and Agent Runtime

**Capabilities:**
- Capture observations from automatic sources (workflow execution, gateway calls, calendar, git, filesystem)
- Capture observations from low-friction manual input (CLI, hotkey, terminal hook)
- Capture observations from scheduled prompts (end-of-day, end-of-week)
- Deduplicate observations at capture time using content + context hash
- Enforce retention policy (90-day granular, compressed thereafter)
- Tag observations with project, goal, decision, and commitment context

**Dependencies:** CAP-001 (Knowledge Management), CAP-004 (Workflow Orchestration), CAP-011 (Identity and Persona Management)

---

### CAP-013 — Executive Function

**Purpose:** Provide continuous attention management, deterministic priority computation, and proactive alerting through the rules engine and attention manager.

**Primary layer:** Layer 6 — Workflow and Agent Runtime (executive daemon)

**Capabilities:**
- Track attention state (active/dormant/forgotten/resurfaced) for all tracked items
- Compute attention decay and trigger state transitions
- Detect stalls (projects without recent attention) and generate alerts
- Score deadline proximity and rank commitments by urgency
- Detect attention fragmentation (excessive active or dormant items)
- Traverse the dependency graph and notify on unblocking events
- Produce deterministic priority rankings (urgency × commitment_weight × momentum)
- Generate attention budget recommendations (suggested focus allocation)

**Dependencies:** CAP-011 (Identity and Persona Management), CAP-012 (Observation and Capture), CAP-004 (Workflow Orchestration)

---

### CAP-014 — Reflection Cycles *(Wyrd domain)*

**Purpose:** Synthesize observations into insights across daily, weekly, monthly, and quarterly cycles. Generate decisions, update the persona, and refine priorities through structured reflection.

**Primary layer:** Layer 6 — Workflow and Agent Runtime (reflection engine); Layer 4 — Knowledge Platform

**Capabilities:**
- Execute daily reflection: reconstruct day, compare planned vs actual, project tomorrow's focus
- Execute weekly reflection: detect patterns, assess momentum, analyse energy, identify tensions
- Execute monthly reflection: strategic alignment, resource allocation, abandonment analysis
- Execute quarterly reflection: outcome analysis, decision audit, value check, learning extraction
- Generate decisions from reflection outputs (focus, abandon, reprioritize, change)
- Update Persona attributes from confirmed reflection insights
- Update priority rankings based on reflection outcomes

**Dependencies:** CAP-011, CAP-012, CAP-013, CAP-003 (AI and Model Management)

---

### CAP-015 — Understanding and Inference

**Purpose:** Detect behavioral patterns, reconcile observed behavior against declared values, build a confidence-weighted model of operator tendencies, and evolve that model through feedback. This is the mechanism that moves the system from remembering to understanding.

**Primary layer:** Layer 6b — Executive Daemon (learning engine); Layer 4 — Knowledge Platform (pattern, contradiction, prediction stores)

**Capabilities:**
- Aggregate raw observations into temporal windows (daily, weekly, monthly, quarterly)
- Detect behavioral patterns: preference-behavior divergence, biases, cycles, attention cliffs, energy correlations, completion signatures, rejection patterns
- Reconcile detected patterns against the canonical persona, producing tension scores
- Compute deterministic confidence scores (0.0–1.0) for every detected pattern using base rate, consistency, recency, specificity, and feedback history
- Generate review candidates for patterns above the surface threshold (>= 0.4 confidence)
- Accept operator feedback on candidates and adjust confidence scores accordingly
- Auto-archive pattern types after 3 consecutive operator rejections within 30 days
- Self-evaluate predictions when their prediction window closes, and adjust source pattern confidence
- Maintain pattern lifecycle: detected → candidate → surfaced → reviewed → active/archived/superseded/promoted

**Dependencies:** CAP-011 (Persona for declared values), CAP-012 (Observations for raw material), CAP-003 (AI and Model Management for pattern detection), CAP-013 (Executive Function for priority context)

---

### CAP-016 — Operator Communication and Review *(Wyrd domain)*

**Purpose:** Provide the dialogue layer through which the operator reviews derived inferences, provides feedback, and maintains sovereignty over what the system has concluded about them. This capability ensures that Wyrd never silently updates the canonical persona.

**Primary layer:** Layer 8 — Experience Layer; `wyrd/src/review/`

**Capabilities:**
- Surface pattern candidates above confidence threshold for operator review
- Present evidence for each candidate in a human-readable, inspectable format
- Accept operator review decisions: accept, reject, snooze, promote to persona, modify
- Record all review decisions as first-class observations (feeding back into confidence scoring)
- Generate periodic review digests (daily or weekly cadence)
- Surface tensions between declared persona values and observed behaviour
- Enable operator to initiate a review session on demand (not only on daemon schedule)
- Provide audit trail of all review decisions

**Dependencies:** CAP-015 (Understanding and Inference for candidates), CAP-011 (Persona for promotion target), CAP-012 (Observations for evidence), CAP-006 (Observability for audit trail)

---

### CAP-017 — Conductor Agent

**Purpose:** Provide a real-time, conversational interface through which the operator directs the system — asking questions, initiating research, generating plans, and summoning assistance — with full context awareness from the Wyrd subsystem.

**Primary layer:** Layer 6c — Conductor Runtime; Layer 8 — Experience Layer (web UI); `platform/conductor/`

**Capabilities:**
- Receive operator instructions in natural language through a local web interface
- Maintain conversation session context across turns (session history, context snapshots)
- Inject Wyrd context (persona, active projects, recent observations) into every model call
- Classify operator intent and route to the appropriate tool (research, plan, summarise, converse)
- Perform research queries through the model gateway with knowledge platform context
- Generate structured plans from operator-described goals
- Summarise documents, observations, or conversation history
- Persist all conversation turns as observations, integrating conductor use into the Wyrd data stream
- Delegate to governed workflows for well-defined subtasks (with operator confirmation)

**Non-capabilities (Phase 6):**
- Does not spawn autonomous sub-agent teams (deferred to Phase 7+)
- Does not modify canonical persona or project data (operator uses CLI for this)
- Does not execute any action requiring operator confirmation without requesting it

**Dependencies:** CAP-003 (Model Gateway for all AI calls), CAP-001 (Knowledge Platform for retrieval), CAP-011 (Persona for context injection), CAP-012 (Observations to write session turns), CAP-013 (Executive Function for priority context)

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
| CAP-011 Identity and Persona Management *(Wyrd)* | Layer 2, Layer 4 |
| CAP-012 Observation and Capture *(Wyrd)* | Layer 4, Layer 6 |
| CAP-013 Executive Function | Layer 6b |
| CAP-014 Reflection Cycles *(Wyrd)* | Layer 6b, Layer 4 |
| CAP-015 Understanding and Inference | Layer 6b, Layer 4 |
| CAP-016 Operator Communication and Review *(Wyrd)* | Layer 8, wyrd/src/review/ |
| CAP-017 Conductor Agent | Layer 6c, Layer 8 |

## Related artifacts

- [`architecture/target-architecture.md`](target-architecture.md) — layers these capabilities map to
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — CAP-xxx ID convention
- [`docs/roadmap.md`](../docs/roadmap.md) — phases that deliver these capabilities
