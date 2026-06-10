# Architecture Principles

**ID:** DOC-003  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define the architectural principles that govern all design, implementation, and governance decisions in AIOS. These principles are not preferences — they are binding constraints. Deviations require an explicit ADR with documented rationale.

---

## Principles

### 1. Local-first by default

Data, computation, and context reside on the local system unless there is an explicit, documented reason to involve remote infrastructure. Remote dependencies are permitted but must be justified, governed, and replaceable.

**Implication:** No component should have an undisclosed dependency on remote services. All remote integrations are surfaced as explicit configuration and governed as external dependencies.

---

### 2. Model-agnostic through a gateway

All AI model interaction flows through a governed model gateway. No application component may call a model directly. The gateway abstracts provider, version, and modality.

**Implication:** Swapping models or providers should require gateway configuration changes only, not application changes. Model selection, rate limiting, cost controls, and audit logging are gateway responsibilities.

---

### 3. Knowledge as a first-class asset

Structured, provenance-tracked knowledge is the primary asset of AIOS. Agents, workflows, and tools are consumers of knowledge — they do not define it. Knowledge must be versioned, attributed, and lifecycle-managed.

**Implication:** Knowledge schema and lifecycle are defined before workflows that consume knowledge. Knowledge assets carry provenance metadata. No knowledge asset is discarded without a lifecycle event record.

---

### 4. Governance before autonomy

Every increase in autonomous capability requires a corresponding increase in governance controls. Autonomy is introduced incrementally through defined stages. No autonomous behaviour is deployed without documented allowed actions, prohibited actions, required controls, and exit criteria.

**Implication:** The autonomy maturity model governs all AI capability deployments. No stage may be skipped. Rollback procedures must exist before any autonomous stage is activated.

---

### 5. Traceability by design

Every capability, decision, workflow, and knowledge asset traces back to a documented intent. Traceability is structural, not optional. The traceability chain is: Vision → Theme → Capability → Solution → Project → Repository → Implementation.

**Implication:** IDs are assigned to artefacts at the appropriate level of the hierarchy. Cross-references between artefacts are maintained. Broken traceability links are treated as defects.

---

### 6. Simple foundations before complex orchestration

Complex orchestration (multi-agent coordination, dynamic planning, recursive self-improvement) is not introduced until the foundation is proven. The foundation is: a stable knowledge store, a governed model gateway, at least one end-to-end inspectable workflow, and operational observability.

**Implication:** Resist premature complexity. Evaluate every proposed abstraction against the current foundation maturity. New abstractions require documented justification.

---

### 7. Canonical versus derived data separation

Canonical knowledge is the authoritative, human-curated, version-controlled record. Derived artefacts (summaries, embeddings, generated content, cached inferences) are always labelled as derived, never promoted to canonical status without human review.

**Implication:** Storage and retrieval systems distinguish canonical from derived. Derived content may be regenerated; canonical content must be preserved. AI-generated content is derived by default.

---

### 8. Human approval for high-impact actions

Actions with significant, difficult-to-reverse consequences require explicit human approval before execution. The definition of "high-impact" is governed by the autonomy maturity model and associated policies. Automated escalation is required when impact is uncertain.

**Implication:** The human approval gate is a first-class architectural component, not an afterthought. Approval events are logged with full context. Override capability must remain available at all autonomy stages.

---

### 9. Security and identity by design

Security, identity, and access policy are not added after the fact. Every component that handles knowledge, model calls, or automated actions operates within an explicit identity and policy context. Least-privilege is the default.

**Implication:** Identity is required before access. Policy is evaluated at the gateway and at every workflow boundary. Security design is reviewed as part of each major capability delivery.

---

### 10. Observability as an operational requirement

The internal state, decisions, and actions of the platform must be inspectable. Observability is not a debugging tool — it is a governance requirement. Metrics, traces, and logs are structured and retained according to defined policy.

**Implication:** All platform components emit structured observability signals. Retention periods are defined. Observability coverage is treated as an exit criterion for each roadmap phase.

---

## Trade-offs

| Principle | Tension | Resolution |
|---|---|---|
| Local-first | May limit model capability or throughput | Acceptable trade-off; capability follows governance |
| Simple foundations | May slow early feature delivery | Intentional; long-term durability is the goal |
| Human approval gates | Reduces automation velocity | Intentional at early stages; relaxed only through maturity model |
| Canonical/derived separation | Increases storage and tooling complexity | Necessary to maintain knowledge integrity |

## Related artifacts

- [`docs/vision.md`](../docs/vision.md) — vision these principles implement
- [`architecture/target-architecture.md`](target-architecture.md) — architecture shaped by these principles
- [`governance/governance-model.md`](../governance/governance-model.md) — governance aligned with these principles
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — autonomy principle detail
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — traceability principle detail
