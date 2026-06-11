# Roadmap

**ID:** DOC-002  
**Status:** Active  
**Last reviewed:** 2026-06-11

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
| Phase 5 | Identity Foundation | ✅ Complete |
| Phase 6 | Wyrd Foundation | 🔄 Active |
| Phase 7 | AI-Assisted Inference | Pending |
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

### Phase 5 — Identity Foundation ✅ Complete

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
- ✅ Persona store is populated with operator-declared facts.
- ✅ Observations are flowing from at least one automatic capture source (git).
- ✅ Projects and commitments have defined lifecycles and are queryable.
- ✅ Personal data governance policy is documented and reviewed.
- ✅ ADR-007 and ADR-008 are accepted and referenced in the capability map.

---

### Phase 6 — Wyrd Foundation 🔄 Active

**Objective:** Establish Wyrd as a named, explicitly bounded subsystem within the AIOS monorepo. Reorganise identity and capture code to reflect the boundary. Build the remaining Phase 5 stores (goals, focus areas). Introduce the first high-quality structural intent capture source (calendar). Build the operator review dialogue.

**Outcomes:**
- The `wyrd/` subsystem exists with a clear README and boundary definition.
- All identity, persona, observation, project, commitment, goal, and focus area code lives under `wyrd/`.
- AIOS core (`platform/executive-daemon/`) contains only inference engine and daemon lifecycle code.
- Calendar is integrated as a structural intent capture source, distinct from behavioral telemetry.
- An operator review interface exists for surfacing pattern candidates and capturing operator feedback.
- The feedback loop between operator review and confidence scoring is operational.
- Signal quality is an explicit architectural concern, governed by ADR-012.

**Deliverables:**
- `wyrd/` — new subsystem directory (ADR-012)
- `wyrd/src/project_store.py` — moved from `platform/executive-daemon/`
- `wyrd/src/goal_store.py` — GoalStore (GL-NNN) and FocusAreaStore (FCA-NNN), new
- `wyrd/src/capture/calendar_capture.py` — calendar as structural intent source
- `wyrd/src/review/` — operator review interface (Markdown digest + CLI submission)
- `wyrd/schema/` — moved and extended schemas
- ADR-012: Wyrd Subsystem Boundary (documents the reorganisation and signal quality principle)
- CAP-016: Operator Communication and Review (new capability)
- Updated target architecture, capability map, vision, glossary

**Exit criteria:**
- `wyrd/` directory exists; `platform/executive-daemon/` contains only engine code.
- All tests pass after the structural reorganisation.
- GoalStore and FocusAreaStore are built and queryable via CLI.
- Calendar capture source is operational (at least one calendar event type captured as an observation).
- Operator can review pattern candidates, accept or reject them, and feedback is recorded.
- ADR-012 is accepted and all documentation is consistent with the Wyrd boundary.

---

### Phase 7 — AI-Assisted Inference

**Objective:** Activate the scheduled AI inference layer (ADR-009 Layer 2, ADR-011) and complete the feedback loop between operator review and the learning engine. Move the system from pattern detection to genuine operator understanding.

**Outcomes:**
- The learning engine runs on a scheduled cycle, calling the model gateway (ADR-002) to analyse aggregated observations.
- Detected patterns, contradictions, and predictions are surfaced via the Wyrd review interface (built in Phase 6).
- Operator feedback flows back into confidence scoring and adjusts pattern type weighting.
- The reconciliation engine surfaces tensions between declared values and observed behaviour.
- Predictions self-evaluate when their window closes, and source pattern confidence is updated.
- No learning engine output modifies the canonical persona without operator review and approval.

**Deliverables:**
- Scheduled AI inference runner: configurable cycle, calls model gateway, governed by ADR-009 Layer 2 rules
- Feedback integration: operator review responses adjust confidence scores and pattern weighting
- Self-evaluation scheduler: evaluates predictions against actuals at window close
- Contradiction surfacing: tensions between persona values and observed behaviour are named and reviewable
- ADR-013 (if required): Scheduled AI Inference Governance

**Exit criteria:**
- At least one pattern type is detected, surfaced, reviewed by the operator, and confidence updated from feedback.
- At least one prediction has been generated and self-evaluated (confirmed or refuted).
- Confidence scoring is deterministic and auditable: any pattern's score is reproducible from the same inputs.
- No learning engine output has modified the canonical persona without operator approval.
- ADR-011 is fully reflected in the target architecture and capability map.

---

### Phase 8 — Governed Autonomy

**Objective:** Progress through defined autonomy stages under explicit governance, enabling selected autonomous operations within bounded scope — for both governed workflows and executive function.

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
- [ADR-011 — Learning Architecture](../adr/0011-learning-architecture.md) — foundation for Phase 7
- [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md) — defining decision for Phase 6
