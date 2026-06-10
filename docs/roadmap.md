# Roadmap

**ID:** DOC-002  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define the phased delivery plan for AIOS. Each phase has explicit outcomes, deliverables, and exit criteria. Phases are sequential; later phases should not begin until exit criteria for the current phase are met.

## Phase status summary

| Phase | Title | Status |
|---|---|---|
| Phase 1 | Repository Bootstrap | ✅ Complete |
| Phase 2 | Architecture Baseline | ✅ Complete |
| Phase 3 | Knowledge Baseline | ✅ Complete |
| Phase 4 | Runtime and Workflow Baseline | ✅ Complete |
| Phase 5 | Identity Foundation | 🔄 Active |
| Phase 6 | Executive Function | Pending |
| Phase 7 | AI-Assisted Executive Function | Pending |
| Phase 8 | Governed Autonomy | Pending |

## Phases

### Phase 1 — Repository Bootstrap ✅ Complete

**Objective:** Establish a governed, navigable repository structure with a documented architecture baseline.

**Outcomes:**
- The repository communicates clear intent and structure to any future contributor or tool.
- All top-level governance artifacts are present and interlinked.
- The ADR process is active and used for significant decisions.

**Deliverables:**
- `README.md` — repository overview
- `docs/vision.md` — long-term vision
- `docs/roadmap.md` — this document
- `architecture/principles.md` — guiding principles
- `architecture/target-architecture.md` — layered architecture
- `architecture/capability-map.md` — capability domains
- `governance/governance-model.md` — governance framework
- `governance/autonomy-maturity-model.md` — autonomy stages
- `governance/traceability-standard.md` — traceability IDs and linking guidance
- `knowledge/knowledge-architecture.md` — knowledge strategy
- `ontology/minimal-viable-ontology.md` — core ontology
- `adr/README.md` — ADR process
- `adr/0001-bootstrap-repository-structure.md` — bootstrap decision record

**Exit criteria:**
- All deliverables present, internally consistent, and interlinked.
- At least one ADR exists and follows the defined format.
- No placeholder sections remain without explicit "TBD" markers and tracking issues.

---

### Phase 2 — Architecture Baseline ✅ Complete

**Objective:** Produce a complete, stable architecture baseline that is sufficient to govern near-term implementation decisions.

**Outcomes:**
- All major capability areas are defined with clear boundaries.
- Traceability IDs are assigned consistently across the baseline.
- A glossary of core terms is established.

**Deliverables:**
- ✅ Expanded `architecture/capability-map.md` with capability-to-layer mapping
- ✅ `docs/glossary.md` — core terminology (DOC-011)
- ✅ ADR-002: model gateway pattern
- ✅ ADR-003: knowledge persistence approach
- ✅ ADR-004: identity model
- ✅ Reviewed and updated `architecture/target-architecture.md`

**Exit criteria:**
- All architecture documents are cross-referenced and internally consistent.
- At least three ADRs exist covering decisions in different domains.
- No open "needs decision" items in the architecture baseline.

---

### Phase 3 — Knowledge Baseline ✅ Complete

**Objective:** Establish the knowledge platform with ingestion, storage, retrieval, and lifecycle governance.

**Outcomes:**
- A working local knowledge store exists.
- Knowledge assets can be created, versioned, and retrieved with provenance.
- The minimal viable ontology is implemented in the knowledge store schema.

**Deliverables:**
- ✅ `platform/knowledge/` — knowledge platform implementation
- ✅ Ingestion pipeline for at least one document format
- ✅ Retrieval interface (not necessarily AI-powered at this stage)
- ✅ Backup and restore capability for the knowledge store
- *(ADR-003 — knowledge persistence approach already accepted in Phase 2)*

**Exit criteria:**
- ✅ Knowledge assets can be created, stored, retrieved, and versioned.
- ✅ Provenance metadata is captured for all ingested assets.
- ✅ Backup and restore procedures are documented and tested.

---

### Phase 4 — Runtime and Workflow Baseline 🔄 Active

**Objective:** Introduce a governed workflow runtime capable of executing bounded, inspectable workflows.

**Outcomes:**
- Workflows can be defined, triggered, executed, and audited.
- All workflow actions are traceable to a documented capability.
- The model gateway mediates all AI model access.

**Deliverables:**
- ✅ `platform/model-gateway/` — model gateway implementation
- ✅ `platform/workflow-runtime/` — workflow runtime implementation
- ✅ `workflows/` — initial workflow definitions (WF-001, WF-002)
- ✅ Workflow audit log (run records in `platform/workflow-runtime/runs/`)
- ✅ ADR-005 — workflow engine technology selection
- ✅ ADR-006 — model gateway technology selection

**Exit criteria:**
- At least two end-to-end workflows execute successfully and are auditable.
- All model calls flow through the gateway.
- Workflow definitions are validated against capability map.

---

### Phase 5 — Identity Foundation 🔄 Active

**Objective:** Establish the persistent identity and observation infrastructure that underpins all executive function capabilities.

**Outcomes:**
- A persistent Persona store exists with declared operator facts, preferences, and values.
- Observations are captured through automatic, manual, and scheduled mechanisms.
- Projects, commitments, goals, and focus areas are first-class entities with lifecycles.
- The naming collision between PROJ (platform delivery) and PRJ (personal project) is resolved.
- Personal data governance domain is defined, including retention, access, and canonical/derived policies.

**Deliverables:**
- `platform/knowledge/persona/` — Persona store (file-based, ADR-003 pattern)
- `platform/knowledge/observations/` — Observation store with multi-layer capture (ADR-008)
- `platform/knowledge/projects/` — Project and commitment stores
- `platform/knowledge/goals/` — Goal and focus area stores
- Personal data governance policy (extends DOC-006)
- ADR-007 (Identity as Domain Object), ADR-008 (Observation Store Architecture)

**Exit criteria:**
- Persona store is populated with operator-declared facts.
- Observations are flowing from at least one automatic capture source.
- Projects and commitments have defined lifecycles and are queryable.
- Personal data governance policy is documented and reviewed.
- ADR-007 and ADR-008 are accepted and referenced in the capability map.

---

### Phase 6 — Executive Function

**Objective:** Deploy the deterministic executive layer — rules engine, attention manager, and executive daemon — providing continuous attention management and prioritization without AI dependency.

**Outcomes:**
- The executive daemon runs continuously, evaluating triggers and managing attention state.
- The rules engine (Layer 1, deterministic) produces stall alerts, deadline warnings, fragmentation notices, and unblocking notifications.
- The attention manager tracks active/dormant/forgotten state with decay functions.
- Projects and commitments drive priority computation through deterministic scoring.
- All executive function outputs are factual and require no model inference.

**Deliverables:**
- `platform/executive-daemon/` — persistent daemon with event loop (ADR-010)
- Rules engine: attention decay, stall detection, deadline scoring, fragmentation detection, dependency traversal
- Attention manager: state transitions, decay model, trigger evaluation
- Priority computation: deterministic scoring (urgency × commitment_weight × momentum)
- CLI: `aios start`, `aios stop`, `aios status`, `aios attention` for operator interaction
- ADR-009 (Executive Reasoning Engine Pattern), ADR-010 (Runtime Model Evolution)

**Exit criteria:**
- Executive daemon runs for 7 consecutive days without crash or state loss.
- Rules engine produces correct stall alerts, deadline warnings, and fragmentation notices.
- Priority ranking is available on demand and reflects current project/commitment state.
- Attention state survives daemon restart (checkpoint/restore verified).
- ADR-009 and ADR-010 are accepted and reflected in the target architecture.

---

### Phase 7 — AI-Assisted Executive Function

**Objective:** Introduce the AI reasoning layer (Layer 2) on top of the deterministic executive foundation, enabling pattern detection, decision support, preference learning, and multi-cycle reflection.

**Outcomes:**
- The AI reasoning layer detects patterns in observation streams, surfacing behavioral insights for operator review.
- Decision context assembly provides historical context for pending decisions.
- Preference learning identifies candidate preferences from observed behavior; all require operator approval.
- The reflection engine operates across daily, weekly, monthly, and quarterly cycles, generating decisions rather than summaries.
- All AI outputs are derived (Principle 7) and require operator review before influencing the persona.

**Deliverables:**
- AI reasoning layer: pattern detection, decision context assembly, preference learning
- Reflection engine: multi-cycle orchestrator with daily/weekly/monthly/quarterly triggers
- Decision store integration with decision context assembly
- Pattern review interface (operator reviews and confirms/declines AI-suggested patterns)
- Preference review interface (operator reviews and confirms/declines AI-suggested preferences)
- Evaluation framework for AI reasoning output quality

**Exit criteria:**
- Pattern detection accuracy meets defined threshold (measured against operator review outcomes).
- Decision context assembly reduces operator decision time for routine decisions (measured).
- At least 4 weekly and 1 monthly reflection cycles have been completed and reviewed.
- No AI output has modified the persona without operator approval.
- Autonomy Stage 1 (AI Assistant) exit criteria satisfied for the executive reasoning domain.

---

### Phase 8 — Governed Autonomy

**Objective:** Progress through defined autonomy stages under explicit governance, enabling selected autonomous operations within bounded scope — for both governed workflows (original Phase 7 intent) and executive function (identity context).

**Outcomes:**
- Autonomous operations are scoped, audited, and reversible.
- The executive reasoning engine may autonomously deprioritize or resurface items within bounded scope and defined thresholds.
- Governance controls escalate automatically when boundaries are approached.
- The system maintains a complete audit trail for all autonomous actions in both runtime domains.

**Deliverables:**
- Autonomy governance controls for executive function (attention, prioritization bounds)
- Escalation and circuit-breaker policies for executive daemon
- Autonomous operation audit reporting across both runtimes
- ADRs for each autonomy stage transition in both domains

**Exit criteria:**
- All exit criteria from the autonomy maturity model are satisfied for each stage reached.
- Executive function autonomy operates within defined bounds without exceeding thresholds.
- No autonomous operation has caused an uncontrolled, irreversible outcome.
- Observability and override capability remain intact at all stages.
- Delivery automation integration (deferred from original Phase 6) may be addressed within this phase.

---

## Dependencies

- Each phase depends on all prior phases reaching their exit criteria.
- The roadmap is reviewed and updated at the end of each phase.
- Significant scope changes require a new ADR.

## Related artifacts

- [`docs/vision.md`](vision.md) — strategic intent this roadmap implements
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — autonomy stages referenced in Phases 7–8
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — traceability applied throughout
- [`adr/README.md`](../adr/README.md) — ADR process used at each phase
- [ADR-007 — Identity as Domain Object](../adr/0007-identity-as-domain-object.md) — foundation for Phase 5
- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md) — foundation for Phase 5
- [ADR-009 — Executive Reasoning Engine Pattern](../adr/0009-executive-reasoning-engine-pattern.md) — design for Phase 6–7
- [ADR-010 — Runtime Model Evolution](../adr/0010-runtime-model-evolution.md) — infrastructure for Phase 6
