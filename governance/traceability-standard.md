# Traceability Standard

**ID:** DOC-008  
**Status:** Active  
**Last reviewed:** 2026-06-11

---

## Purpose

Define the traceability hierarchy, identifier conventions, metadata expectations, and linking guidance for all AIOS artefacts. Traceability is not optional — every documented artefact is positioned in the hierarchy, and broken links are treated as defects.

## Traceability chain

Every artefact in AIOS traces to a node in the following hierarchy:

```
Vision (VIS)
  └── Theme (THEME)
        └── Capability (CAP)
              └── Solution (SOL)
                    └── Project (PROJ)
                          └── Repository (REP)
                                └── Implementation (ADR / WF / DOC)
```

Upward traceability: every artefact references its parent in the chain.  
Downward traceability: higher-level artefacts list their known children.

---

## Identifier conventions

| Level | Prefix | Example | Format |
|---|---|---|---|
| Vision | `VIS` | `VIS-001` | `VIS-NNN` |
| Theme | `THEME` | `THEME-001` | `THEME-NNN` |
| Capability | `CAP` | `CAP-001` | `CAP-NNN` |
| Solution | `SOL` | `SOL-001` | `SOL-NNN` |
| Project (deprecated) | `PROJ` | `PROJ-001` | `PROJ-NNN` |
| Repository | `REP` | `REP-001` | `REP-NNN` |
| Architecture Decision Record | `ADR` | `ADR-001` | `ADR-NNN` |
| Workflow | `WF` | `WF-001` | `WF-NNN` |
| Document | `DOC` | `DOC-001` | `DOC-NNN` |
| Persona | `PRS` | `PRS-001` | `PRS-NNN` |
| Project (universal) | `PRJ` | `PRJ-001` | `PRJ-NNN` |
| Observation | `OBS` | `OBS-001` | `OBS-NNN` |
| Goal | `GL` | `GL-001` | `GL-NNN` |
| Decision | `DEC` | `DEC-001` | `DEC-NNN` |
| Preference | `PRF` | `PRF-001` | `PRF-NNN` |
| Belief | `BLF` | `BLF-001` | `BLF-NNN` |
| Habit | `HBT` | `HBT-001` | `HBT-NNN` |
| Relationship | `REL` | `REL-001` | `REL-NNN` |
| Reflection | `RFL` | `RFL-001` | `RFL-NNN` |
| Commitment | `CMT` | `CMT-001` | `CMT-NNN` |
| Focus Area | `FCA` | `FCA-001` | `FCA-NNN` |
| Responsibility | `RSP` | `RSP-001` | `RSP-NNN` |
| Opportunity | `OPP` | `OPP-001` | `OPP-NNN` |
| Risk | `RSK` | `RSK-001` | `RSK-NNN` |
| Constraint | `CON` | `CON-001` | `CON-NNN` |
| Wyrd subsystem artefact | `WYR` | `WYR-001` | `WYR-NNN` |

`NNN` is a zero-padded three-digit integer. IDs are assigned sequentially within each prefix. IDs are never reused.

---

## Assigned identifiers (bootstrap set)

### Vision

| ID | Description |
|---|---|
| VIS-001 | AIOS — Personal AI Operating System |

### Themes

| ID | Description |
|---|---|
| THEME-001 | Architecture and Governance Foundation |
| THEME-002 | Knowledge Platform |
| THEME-003 | AI and Model Management |
| THEME-004 | Workflow and Agent Runtime |
| THEME-005 | Delivery Integration |
| THEME-006 | Controlled Autonomy |

### Capabilities

See [`architecture/capability-map.md`](../architecture/capability-map.md) for the full list. Bootstrap set:

| ID | Description |
|---|---|
| CAP-001 | Knowledge Management |
| CAP-002 | Architecture Governance |
| CAP-003 | AI and Model Management |
| CAP-004 | Workflow Orchestration |
| CAP-005 | Delivery Automation |
| CAP-006 | Observability |
| CAP-007 | Security and Policy |
| CAP-008 | Evaluation |
| CAP-009 | Memory and Provenance |
| CAP-010 | User and Operator Experience |
| CAP-011 | Identity and Persona Management *(Wyrd domain)* |
| CAP-012 | Observation and Capture *(Wyrd domain)* |
| CAP-013 | Executive Function |
| CAP-014 | Reflection Cycles *(Wyrd domain)* |
| CAP-015 | Understanding and Inference |
| CAP-016 | Operator Communication and Review *(Wyrd domain)* |
| CAP-017 | Conductor Agent |

### Repositories

| ID | Description |
|---|---|
| REP-001 | `SkogsErik/aios` — this repository (AIOS core + Wyrd subsystem) |

### Documents

| ID | Description |
|---|---|
| DOC-001 | `docs/vision.md` |
| DOC-002 | `docs/roadmap.md` |
| DOC-003 | `architecture/principles.md` |
| DOC-004 | `architecture/target-architecture.md` |
| DOC-005 | `architecture/capability-map.md` |
| DOC-006 | `governance/governance-model.md` |
| DOC-007 | `governance/autonomy-maturity-model.md` |
| DOC-008 | `governance/traceability-standard.md` (this document) |
| DOC-009 | `knowledge/knowledge-architecture.md` |
| DOC-010 | `ontology/minimal-viable-ontology.md` |
| DOC-011 | `docs/glossary.md` |
| DOC-012 | `platform/knowledge/docs/backup-restore-runbook.md` |
| DOC-013 | `platform/model-gateway/README.md` |
| DOC-014 | `platform/workflow-runtime/README.md` |
| DOC-015 | `workflows/README.md` |
| DOC-016 | `architecture/identity-centric-pivot-analysis.md` |
| DOC-017 | `architecture/executive-cognition-analysis.md` |
| DOC-018 | `architecture/pivot-readiness-assessment.md` |
| DOC-019 | `wyrd/README.md` *(planned — Phase 6)* |
| DOC-020 | `platform/conductor/README.md` *(planned — Phase 6)* |

### Architecture Decision Records

| ID | Description |
|---|---|
| ADR-001 | Bootstrap repository structure (`adr/0001-bootstrap-repository-structure.md`) |
| ADR-002 | Model gateway pattern (`adr/0002-model-gateway-pattern.md`) |
| ADR-003 | Knowledge persistence approach (`adr/0003-knowledge-persistence-approach.md`) |
| ADR-004 | Identity model (`adr/0004-identity-model.md`) |
| ADR-005 | Workflow engine technology selection (`adr/0005-workflow-engine-technology.md`) |
| ADR-006 | Model gateway technology selection (`adr/0006-model-gateway-technology.md`) |
| ADR-007 | Identity as Domain Object (`adr/0007-identity-as-domain-object.md`) |
| ADR-008 | Observation Store Architecture (`adr/0008-observation-store-architecture.md`) |
| ADR-009 | Executive Reasoning Engine Pattern (`adr/0009-executive-reasoning-engine-pattern.md`) |
| ADR-010 | Runtime Model Evolution (`adr/0010-runtime-model-evolution.md`) |
| ADR-011 | Learning Architecture (`adr/0011-learning-architecture.md`) |
| ADR-012 | Wyrd Subsystem Boundary (`adr/0012-wyrd-subsystem-boundary.md`) |
| ADR-013 | Conductor Agent Design (`adr/0013-conductor-agent-design.md`) |

### Workflows

| ID | Description |
|---|---|
| WF-001 | Knowledge Asset Ingestion (`workflows/WF-001-knowledge-ingest.yaml`) |
| WF-002 | Knowledge Store Search (`workflows/WF-002-knowledge-search.yaml`) |

---

## Document metadata standard

All documents must include the following header:

```markdown
**ID:** DOC-NNN (or ADR-NNN, WF-NNN, etc.)
**Status:** Draft | Active | Superseded | Deprecated
**Last reviewed:** YYYY-MM-DD
```

Additional optional metadata:

```markdown
**Supersedes:** DOC-NNN
**Superseded by:** DOC-NNN
**Parent:** THEME-NNN or CAP-NNN
**Related:** DOC-NNN, ADR-NNN
```

---

## Linking guidance

### Within a document

Reference related artefacts using their ID and a relative file link:

```markdown
See [DOC-003](../architecture/principles.md) for architecture principles.
```

### In ADRs

ADRs must reference the capabilities and themes they affect:

```markdown
**Affects:** CAP-001, THEME-002
```

### Traceability validation

At each roadmap phase transition, the following checks are performed:

1. All documents have a valid ID in the header.
2. All referenced IDs exist in this traceability register.
3. All capabilities in the capability map have at least one implementing ADR or documented roadmap phase.
4. No document references an ID that has been deprecated without also referencing its replacement.

Broken traceability is recorded as a defect and resolved before the phase transition is approved.

---

## Evolution

This register is maintained in this document for the bootstrap phase. Once the platform reaches Phase 3 (Knowledge Baseline), traceability data will be migrated to the knowledge store for machine-queryable access. The schema in this document defines the target structure for that migration.

## Related artifacts

- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP IDs
- [`adr/README.md`](../adr/README.md) — ADR IDs and process
- [`docs/roadmap.md`](../docs/roadmap.md) — phase transitions that trigger traceability validation
