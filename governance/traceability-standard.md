# Traceability Standard

**ID:** DOC-008  
**Status:** Active  
**Last reviewed:** 2026-06-10

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
| Project | `PROJ` | `PROJ-001` | `PROJ-NNN` |
| Repository | `REP` | `REP-001` | `REP-NNN` |
| Architecture Decision Record | `ADR` | `ADR-001` | `ADR-NNN` |
| Workflow | `WF` | `WF-001` | `WF-NNN` |
| Document | `DOC` | `DOC-001` | `DOC-NNN` |

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

### Repositories

| ID | Description |
|---|---|
| REP-001 | `SkogsErik/aios` — this repository |

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

### Architecture Decision Records

| ID | Description |
|---|---|
| ADR-001 | Bootstrap repository structure (`adr/0001-bootstrap-repository-structure.md`) |

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
