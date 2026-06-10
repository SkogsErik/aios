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
| Phase 3 | Knowledge Baseline | 🔄 Active |
| Phase 4 | Runtime and Workflow Baseline | Pending |
| Phase 5 | Human-in-the-Loop Assistance | Pending |
| Phase 6 | Delivery Integration | Pending |
| Phase 7 | Controlled Autonomy | Pending |

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

### Phase 3 — Knowledge Baseline 🔄 Active

**Objective:** Establish the knowledge platform with ingestion, storage, retrieval, and lifecycle governance.

**Outcomes:**
- A working local knowledge store exists.
- Knowledge assets can be created, versioned, and retrieved with provenance.
- The minimal viable ontology is implemented in the knowledge store schema.

**Deliverables:**
- `platform/knowledge/` — knowledge platform implementation
- Ingestion pipeline for at least one document format
- Retrieval interface (not necessarily AI-powered at this stage)
- Backup and restore capability for the knowledge store
- *(ADR-003 — knowledge persistence approach already accepted in Phase 2)*

**Exit criteria:**
- Knowledge assets can be created, stored, retrieved, and versioned.
- Provenance metadata is captured for all ingested assets.
- Backup and restore procedures are documented and tested.

---

### Phase 4 — Runtime and Workflow Baseline

**Objective:** Introduce a governed workflow runtime capable of executing bounded, inspectable workflows.

**Outcomes:**
- Workflows can be defined, triggered, executed, and audited.
- All workflow actions are traceable to a documented capability.
- The model gateway mediates all AI model access.

**Deliverables:**
- `platform/model-gateway/` — model gateway implementation
- `workflows/` — initial workflow definitions
- Workflow audit log
- ADRs for workflow engine and model gateway technology selections

**Exit criteria:**
- At least two end-to-end workflows execute successfully and are auditable.
- All model calls flow through the gateway.
- Workflow definitions are validated against capability map.

---

### Phase 5 — Human-in-the-Loop Assistance

**Objective:** Introduce AI-assisted capabilities with explicit human approval gates for all significant actions.

**Outcomes:**
- AI assistance is available for knowledge enrichment, document drafting, and workflow suggestions.
- All AI-suggested actions require human approval before execution.
- The system operates at Autonomy Stage 2 (AI Assistant) as defined in the autonomy maturity model.

**Deliverables:**
- Human approval interface for AI-suggested actions
- Observability dashboard for AI actions and approvals
- Evaluation framework for AI output quality
- ADR for human-in-the-loop architecture

**Exit criteria:**
- All AI-suggested actions are captured with full provenance.
- Human approval rate and override rate are measurable.
- No autonomous action is taken without explicit approval.
- Autonomy Stage 2 exit criteria satisfied.

---

### Phase 6 — Delivery Integration

**Objective:** Integrate AIOS with software delivery workflows, enabling AI-assisted development and automation.

**Outcomes:**
- AIOS can assist with code generation, review, and documentation.
- Delivery workflows are governed by the same traceability and approval standards as other workflows.
- Integration with version control and CI/CD is operational.

**Deliverables:**
- `platform/delivery/` — delivery integration implementation
- Delivery workflow definitions
- ADRs for delivery integration decisions

**Exit criteria:**
- At least one delivery workflow is operational and auditable.
- All delivery automation is governed and traceable.
- Autonomy Stage 3 exit criteria satisfied (if applicable).

---

### Phase 7 — Controlled Autonomy

**Objective:** Progress through defined autonomy stages under explicit governance, enabling selected autonomous operations within bounded scope.

**Outcomes:**
- Autonomous operations are scoped, audited, and reversible.
- Governance controls escalate automatically when boundaries are approached.
- The system maintains a complete audit trail for all autonomous actions.

**Deliverables:**
- Autonomy governance controls implementation
- Escalation and circuit-breaker policies
- Autonomous operation audit reporting
- ADRs for each autonomy stage transition

**Exit criteria:**
- All exit criteria from the autonomy maturity model are satisfied for each stage reached.
- No autonomous operation has caused an uncontrolled, irreversible outcome.
- Observability and override capability remain intact at all stages.

---

## Dependencies

- Each phase depends on all prior phases reaching their exit criteria.
- The roadmap is reviewed and updated at the end of each phase.
- Significant scope changes require a new ADR.

## Related artifacts

- [`docs/vision.md`](vision.md) — strategic intent this roadmap implements
- [`governance/autonomy-maturity-model.md`](../governance/autonomy-maturity-model.md) — autonomy stages referenced in Phases 5–7
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — traceability applied throughout
- [`adr/README.md`](../adr/README.md) — ADR process used at each phase
