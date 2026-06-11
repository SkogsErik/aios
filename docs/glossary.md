# Glossary

**ID:** DOC-011  
**Status:** Active  
**Last reviewed:** 2026-06-11  
**Parent:** THEME-001

---

## Purpose

Define the core terminology used across AIOS artefacts. Consistent terminology reduces ambiguity and ensures that documents, decisions, and conversations share a common frame of reference.

Terms are defined at the precision needed to disambiguate. This glossary is intentionally concise; it is not a comprehensive ontology. For formal entity definitions and relationships, see [`ontology/minimal-viable-ontology.md`](../ontology/minimal-viable-ontology.md).

---

## Terms

### Agent Role
A bounded role that an AI agent may fulfil within a governed workflow. Agent roles are a late-stage abstraction derived from capabilities and workflows. They do not define capabilities; they express how capabilities are delivered autonomously at an appropriate autonomy stage.

See: [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md)

---

### Architecture Decision Record (ADR)
A short document that captures a significant architectural decision: its context, the options considered, the decision made, its rationale, and its known consequences. ADRs are the primary mechanism for making design decisions explicit, traceable, and revisable.

Identifier prefix: `ADR`  
See: [`adr/README.md`](../adr/README.md)

---

### Audit Trail
An immutable, ordered record of significant platform actions, approvals, and decisions. The audit trail satisfies traceability and accountability requirements and supports override and investigation workflows.

---

### Autonomy Stage
A defined level of AI autonomy within the AIOS autonomy maturity model. Stages are numbered 1–5, from fully manual (Stage 1) to bounded agentic operation (Stage 5). Progression between stages requires satisfying documented exit criteria and governance approval.

See: [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md)

---

### Canonical Knowledge
Knowledge assets that are authoritative, versioned, provenance-tracked, and managed under the knowledge lifecycle. Canonical knowledge is the primary input to workflows and AI-assisted operations. It is never silently overwritten.

Contrast with: Derived Knowledge

---

### Capability
A defined, bounded area of platform functionality. Capabilities describe what the system must be able to do; they are the primary unit for scoping work, assigning traceability IDs, and evaluating where new components belong. Capabilities are not implementation components.

Identifier prefix: `CAP`  
See: [`architecture/capability-map.md`](../architecture/capability-map.md)

---

### Circuit Breaker
A governance control that halts or escalates automated operations when a defined boundary condition is reached — for example, an error rate threshold, a cost budget, or an autonomy scope violation. Circuit breakers are a safeguard against runaway automation.

---

### Derived Knowledge (Derived Artefact)
A knowledge item generated from canonical knowledge through transformation, inference, or AI processing. Derived artefacts are labelled as such, trace to their canonical source, and are regenerable. They are not considered authoritative on their own.

Contrast with: Canonical Knowledge

---

### Document
A governed documentation artefact such as a vision statement, architecture standard, runbook, or governance policy. Documents are version-controlled, carry traceability IDs, and are subject to the document metadata standard.

Identifier prefix: `DOC`  
See: [`governance/traceability-standard.md`](../governance/traceability-standard.md)

---

### Escalation
The act of routing a platform action or decision to a human operator when it exceeds the currently permitted autonomy scope, cost threshold, or risk level. Escalation policies define when and how escalation occurs.

---

### Evaluation
A structured assessment of the quality, correctness, or safety of a knowledge asset, AI output, or workflow outcome. Evaluations produce a record that supports traceability and continuous improvement.

See: `CAP-008` in [`architecture/capability-map.md`](../architecture/capability-map.md)

---

### Governance
The set of controls, processes, policies, and review mechanisms that ensure the platform evolves in a controlled, traceable, and auditable way. Governance is not optional overhead — it is the mechanism by which autonomy is earned and trust is maintained.

See: [`governance/governance-model.md`](../governance/governance-model.md)

---

### Human Approval Gate
A defined checkpoint in a workflow or automated process where execution pauses and an operator must explicitly approve the proposed action before it proceeds. Human approval gates are the primary mechanism for maintaining human oversight at appropriate autonomy stages.

---

### Identity Context
The authenticated identity associated with a request or operation — either an operator identity or a service identity. All requests at Layer 3 and above carry an identity context, evaluated against access control policies.

See: `ADR-004` — Identity Model; [`architecture/target-architecture.md`](../architecture/target-architecture.md) Layer 2

---

### Knowledge Asset
Any document, data record, research note, decision record, or structured artefact managed in the Knowledge Platform. Knowledge assets have provenance metadata, lifecycle status, and versioning.

See: [`knowledge/knowledge-architecture.md`](../knowledge/knowledge-architecture.md)

---

### Knowledge Platform
The platform layer (Layer 4) responsible for storing, retrieving, lifecycle-managing, and provenance-tracking all canonical knowledge assets. It is the foundation on which AI-assisted workflows and agent roles operate.

See: [`architecture/target-architecture.md`](../architecture/target-architecture.md) Layer 4

---

### Layer
A distinct horizontal tier in the AIOS target architecture. Layers have defined responsibilities and boundaries. Higher layers depend on lower layers; lower layers do not call into higher layers. Cross-layer dependencies require explicit documentation.

See: [`architecture/target-architecture.md`](../architecture/target-architecture.md)

---

### Local-first
An architectural stance in which data, computation, and context remain on the local system by default. Remote dependencies are introduced only when they provide compelling, well-governed value and are explicitly approved. Local-first is a core AIOS design principle.

See: [`architecture/principles.md`](../architecture/principles.md)

---

### Model Gateway
The governed, auditable interface (Layer 3) through which all AI model calls flow. The model gateway abstracts provider, version, and modality, and enforces rate limits, cost controls, audit logging, and safety policies. No platform component may call a model directly, bypassing the gateway.

See: `ADR-002` — Model Gateway Pattern; [`architecture/target-architecture.md`](../architecture/target-architecture.md) Layer 3

---

### Model-agnostic
A design property meaning no platform component has a hard dependency on a specific AI model or provider. All model interaction is mediated through the model gateway. This property ensures the platform can adapt to model changes without structural modification.

---

### Ontology
The formal (or semi-formal) definition of the entities, relationships, and terminology that govern AIOS artefacts. The minimal viable ontology is intentionally small and evolvable.

See: [`ontology/minimal-viable-ontology.md`](../ontology/minimal-viable-ontology.md)

---

### Policy
A governance rule that constrains the behaviour of platform components, workflows, or agent roles. Policies are evaluated at runtime (e.g., access control) and at design time (e.g., architectural principles). Policies are defined as governance artefacts, not implicit conventions.

---

### Provenance
The recorded origin, authorship, creation date, and transformation history of a knowledge asset or derived artefact. Provenance is a first-class property of all canonical knowledge. It supports trust, auditability, and traceability.

---

### Repository
A version-controlled code or documentation store that implements or documents capabilities. The `SkogsErik/aios` repository (`REP-001`) is the single monorepo for all AIOS architecture and future implementation artefacts.

Identifier prefix: `REP`

---

### Solution
A defined approach to realising one or more capabilities, typically spanning one or more projects. Solutions are intermediate nodes in the traceability chain between capabilities and repositories.

Identifier prefix: `SOL`

---

### Theme
A strategic theme that organises capabilities under the vision. Themes provide mid-level groupings that link the high-level vision to specific capability areas.

Identifier prefix: `THEME`  
See: [`governance/traceability-standard.md`](../governance/traceability-standard.md)

---

### Traceability
The property of an artefact or decision being explicitly linked to its originating intent in the traceability hierarchy (Vision → Theme → Capability → … → Implementation). Traceability is not optional in AIOS; broken traceability links are treated as defects.

See: [`governance/traceability-standard.md`](../governance/traceability-standard.md)

---

### Vision
The highest-level statement of intent for AIOS. The vision governs strategic direction and defines what AIOS is and is not intended to become.

Identifier prefix: `VIS`  
See: [`docs/vision.md`](vision.md)

---

### Workflow
A defined, executable sequence of governed steps that realises a capability. Workflows are owned by Layer 6, are bounded by a documented capability, and produce a full audit log on execution.

Identifier prefix: `WF`  
See: [`architecture/target-architecture.md`](../architecture/target-architecture.md) Layer 6

---

### Wyrd
The operator understanding subsystem of AIOS. Wyrd holds the persistent, evolving model of who the operator is — declared facts, values, preferences, projects, commitments, goals, and the observation stream that feeds the inference pipeline. It also owns all capture sources and the operator review interface.

The name derives from Old Norse *wyrd* (fate, personal narrative, the thread of a life). A subsystem that builds a genuine model of an operator's identity over time earns that name.

Wyrd is a named domain boundary within the AIOS monorepo (`wyrd/`), not a separate system. AIOS core reads from Wyrd's stores through the shared filesystem contract (ADR-003). Wyrd is designed to be extractable as an independent repository once the boundary is stable and extraction triggers are met (see ADR-012).

Contrast with: AIOS core (inference engines, daemon lifecycle, model gateway, workflow runtime)  
See: [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md); [`wyrd/README.md`](../wyrd/README.md) *(Phase 6)*

---

### Structural Intent Signal
An observable input that reflects a deliberate commitment of the operator's attention or resources. Structural intent signals are high-quality inputs for operator modeling because they capture *what the operator meant*, not merely *what they did*.

Examples: calendar entries (explicit time commitments), declared priorities, written observations, kept or broken commitments, reasoned decisions with stated rationale.

Contrast with: Behavioral Telemetry  
See: [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md) (signal quality principle)

---

### Behavioral Telemetry
High-volume, passively collected signals about operator activity — keystroke cadence, scroll patterns, application focus time, URL visit history, mouse activity, idle detection. These signals capture *what the operator did* but not *what they meant*. They require significant inference to extract meaningful signals and carry privacy risks.

Behavioral telemetry is explicitly *not* the foundation of Wyrd's operator model. It may be introduced at a later stage, but only through a separate governance decision. Structural intent signals are preferred at every stage where both are available.

Contrast with: Structural Intent Signal  
See: [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md) (signal quality principle)

---

## Related artifacts

- [`ontology/minimal-viable-ontology.md`](../ontology/minimal-viable-ontology.md) — formal entity definitions
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — identifier conventions
- [`architecture/capability-map.md`](../architecture/capability-map.md) — capability definitions
- [`architecture/principles.md`](../architecture/principles.md) — principles that use these terms
