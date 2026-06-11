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

### Phase 6 — Wyrd Foundation + Conductor MVP 🔄 Active

**Objective:** Two parallel tracks. Track A closes the Wyrd structural work defined in ADR-012. Track B delivers the Conductor (ADR-013) — the interactive layer that gives AIOS immediate daily utility.

**Why two tracks in one phase:** Wyrd provides the identity context that makes the Conductor genuinely useful. Both are needed for Phase 6 to be complete. The Wyrd structural work is smaller (~days); the Conductor is the primary effort.

---

#### Track A — Wyrd Foundation

**Objective:** Establish `wyrd/` as a named, explicitly bounded subsystem. Reorganise identity and capture code. Build goal and focus area stores.

**Outcomes:**
- The `wyrd/` subsystem exists with a clear README and boundary definition (ADR-012)
- All identity, persona, observation, project, commitment, goal, and focus area code lives under `wyrd/`
- `platform/executive-daemon/` contains only inference engine and daemon lifecycle code
- GoalStore and FocusAreaStore are operational and CLI-queryable

**Deliverables:**
- `wyrd/` directory scaffold and README (DOC-019)
- `wyrd/src/project_store.py` — moved from `platform/executive-daemon/`
- `wyrd/src/goal_store.py` — GoalStore (GL-NNN) and FocusAreaStore (FCA-NNN)
- `wyrd/src/capture/` — moved from `platform/executive-daemon/`
- `wyrd/schema/` — moved and extended schemas
- CLI: `aios goal add/list/show`, `aios focus add/list`

**Track A exit criteria:**
- `wyrd/` directory exists; all tests pass after moves
- GoalStore and FocusAreaStore built and queryable
- `platform/executive-daemon/` contains no identity store code

---

#### Track B — Conductor MVP

**Objective:** Build a local, conversational interface that the operator can use today to research, plan, and get assistance — with context from Wyrd injected into every call.

**Outcomes:**
- The operator can open a browser, type a question or instruction, and receive a useful response
- The conductor has context about the operator's persona, active projects, and recent observations
- Conductor sessions are persisted as YAML and session turns become observations
- Research, plan, and summarise tools are functional

**Deliverables:**
- `platform/conductor/` — new module (DOC-020)
- `src/session.py` — conversation session management (YAML persistence, ADR-003)
- `src/context.py` — Wyrd context assembly for every model call
- `src/dispatch.py` — intent classification and tool routing
- `src/tools/` — research, plan, summarise tools
- `src/api.py` — FastAPI HTTP endpoint (localhost)
- `web/index.html` — minimal chat UI
- ADR-013 accepted and referenced

**Track B exit criteria:**
- Conductor HTTP server starts and serves the web UI
- Operator can send a message and receive a model-backed response
- Context injection is verified: persona and active projects appear in model call context
- Session is persisted after conversation
- Session turns are recorded as observations in the Wyrd store
- At least 25 tests passing

---

**Phase 6 combined exit criteria:**
- All Track A and Track B exit criteria met
- ADR-012 and ADR-013 both accepted
- All documentation consistent (capability map, target architecture, traceability, glossary)
- No broken traceability links

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
- [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md) — defining decision for Phase 6 Track A
- [ADR-013 — Conductor Agent Design](../adr/0013-conductor-agent-design.md) — defining decision for Phase 6 Track B
