# Minimal Viable Ontology

**ID:** DOC-010  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define the minimal set of entities and relationships needed to govern AIOS artefacts, support traceability, and enable future machine-readable evolution. The ontology is intentionally small and evolvable. Complexity is added only when justified by demonstrated need.

---

## Why start minimal

An ontology that is too large becomes a maintenance burden and a barrier to adoption. A minimal ontology:

- Captures only the concepts that appear repeatedly across governance, architecture, and knowledge artefacts
- Enables consistent terminology without over-specifying structure
- Can be evolved incrementally as the platform matures
- Is expressible in plain text (this document) before requiring formal tooling

As AIOS progresses through later roadmap phases, this ontology may be expressed in a machine-readable format (e.g. OWL, JSON-LD, or a knowledge graph schema). Any such evolution will be recorded as an ADR.

---

## Entities

### Vision
The highest-level statement of intent for AIOS.  
**Identifier prefix:** `VIS`  
**Example:** `VIS-001` — AIOS Personal AI Operating System

### Theme
A strategic theme that organises capabilities under the vision.  
**Identifier prefix:** `THEME`  
**Example:** `THEME-001` — Architecture and Governance Foundation

### Capability
A defined, bounded area of platform capability.  
**Identifier prefix:** `CAP`  
**Example:** `CAP-001` — Knowledge Management

### Project
A bounded unit of delivery work that realises one or more capabilities.  
**Identifier prefix:** `PROJ`  
**Example:** `PROJ-001` — Knowledge Platform Bootstrap

### Repository
A version-controlled code or documentation repository that implements or documents capabilities.  
**Identifier prefix:** `REP`  
**Example:** `REP-001` — `SkogsErik/aios`

### ADR
An Architecture Decision Record capturing a significant decision, its context, options, rationale, and consequences.  
**Identifier prefix:** `ADR`  
**Example:** `ADR-001` — Bootstrap Repository Structure

### Document
A governed documentation artefact: vision, principles, standards, architecture documents, runbooks.  
**Identifier prefix:** `DOC`  
**Example:** `DOC-001` — `docs/vision.md`

### KnowledgeAsset
A canonical or derived knowledge item managed in the Knowledge Platform.  
No fixed prefix — domain-specific identifiers apply.  
**Example:** A research note, annotated source, or domain model entry

### Workflow
A defined, executable sequence of governed steps.  
**Identifier prefix:** `WF`  
**Example:** `WF-001` — Knowledge Ingestion Workflow

### AgentRole
A bounded role that an AI agent may fulfil within a governed workflow. Agent roles are a late-stage abstraction; they are not defined until workflows exist to host them.  
**Note:** Agent roles are derived from capabilities and workflows. They do not define capabilities.

### Policy
A governance rule that constrains the behaviour of platform components, workflows, or agent roles.  
**Governed by:** [`governance/governance-model.md`](../governance/governance-model.md)

### Evaluation
A structured assessment of the quality, correctness, or safety of a knowledge asset, AI output, or workflow outcome.  
**Governed by:** CAP-008 in the capability map

---

## Relationships

| Relationship | Description | Example |
|---|---|---|
| `supports` | A lower-level entity contributes to a higher-level intent | `THEME-001 supports VIS-001` |
| `realizes` | An entity concretely implements an abstract capability or intent | `PROJ-001 realizes CAP-001` |
| `belongs_to` | An entity is scoped to a parent entity | `CAP-001 belongs_to THEME-002` |
| `implemented_by` | A capability or decision is implemented by a repository or project | `CAP-001 implemented_by REP-001` |
| `documented_in` | An entity is described by a document | `CAP-001 documented_in DOC-005` |
| `decided_by` | A design choice is governed by an ADR | `REP-001 structure decided_by ADR-001` |
| `derived_from` | A derived artefact originates from a canonical source | `Embedding derived_from KnowledgeAsset` |
| `evidenced_by` | A claim is supported by a referenced artefact | `Stage transition evidenced_by Evaluation` |
| `governed_by` | An entity is subject to a governance control or policy | `WF-001 governed_by Policy` |
| `evaluated_by` | An entity is assessed by an evaluation | `KnowledgeAsset evaluated_by Evaluation` |
| `depends_on` | An entity requires another entity to function | `CAP-004 depends_on CAP-003` |

---

## Ontology evolution path

| Phase | Ontology state |
|---|---|
| Phase 1–2 | Plain text in this document; informally applied |
| Phase 3 | Ontology reflected in knowledge store schema; structured metadata |
| Phase 4+ | Consider formal expression (JSON-LD, OWL, graph schema); decision requires ADR |

Promotion to a machine-readable format will be driven by operational need (e.g., the need for automated traceability validation or knowledge graph queries), not by theoretical completeness.

---

## What is deliberately excluded

The following concepts are deliberately absent from the minimal ontology:

- Fine-grained agent behaviour models (too early)
- Multi-user or organisational hierarchy (out of scope for personal AIOS)
- Financial or resource allocation entities (not yet relevant)
- Full provenance graph (partially covered by `derived_from`; full graph in Phase 3+)

Additions to the ontology require a documented justification (ADR or governance note) explaining why the concept cannot be adequately expressed with existing entities and relationships.

---

## Related artifacts

- [`knowledge/knowledge-architecture.md`](../knowledge/knowledge-architecture.md) — knowledge entities this ontology governs
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — identifier conventions
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP entities
