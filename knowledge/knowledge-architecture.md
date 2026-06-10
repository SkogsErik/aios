# Knowledge Architecture

**ID:** DOC-009  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

Define how knowledge is categorised, stored, provenance-tracked, lifecycle-managed, and retrieved in AIOS. This document governs the design of the Knowledge Platform (Layer 4) and informs the ontology, workflows, and evaluation capabilities.

---

## Knowledge categories

### 1. Architecture and Governance Knowledge

Records of architectural decisions, principles, standards, and governance artefacts. These are the authoritative design intent of the platform.

- Examples: ADRs, architecture principles, capability maps, governance policies
- Canonical: Yes
- Source: Human-authored, version-controlled in this repository
- Sensitive: Low

### 2. Domain Knowledge

Structured understanding of subject domains relevant to the operator's work. This is the long-term intellectual asset of AIOS.

- Examples: Research notes, domain models, reference materials, annotated sources
- Canonical: Yes (for curated assets); Derived for AI-enriched summaries
- Source: Operator-ingested or AI-assisted with human review
- Sensitive: Variable

### 3. Operational Knowledge

Records of platform behaviour, incidents, decisions, and runbook procedures.

- Examples: Incident records, operational runbooks, configuration decisions
- Canonical: Yes
- Source: Operator-authored, system-generated events
- Sensitive: Low to Medium

### 4. Contextual and Working Memory

Ephemeral or semi-persistent context used by workflows and AI assistants to support active tasks. Not intended to be canonical.

- Examples: Session context, in-progress research, workflow state
- Canonical: No — derived and transient
- Source: System-generated or workflow-produced
- Sensitive: Variable

### 5. Derived and Generated Knowledge

Content produced by AI inference from canonical sources. Always labelled as derived and subject to human review before promotion.

- Examples: Summaries, embeddings, generated drafts, extracted entities
- Canonical: No — derived until human-reviewed and explicitly promoted
- Source: Model gateway outputs
- Sensitive: Inherits sensitivity from source

---

## Canonical versus derived knowledge

| Attribute | Canonical | Derived |
|---|---|---|
| Authoritative | Yes | No |
| Human-reviewed | Yes (required) | No (unless promoted) |
| Version-controlled | Yes | Optional |
| Regenerable | No | Yes |
| Promotion path | N/A | Requires human review and explicit lifecycle transition |
| Backup required | Yes | Desirable but regenerable if lost |

AI-generated content is **always derived** at creation time. Promotion to canonical requires an explicit human review event, which is logged with provenance.

---

## Provenance metadata

Every knowledge asset carries the following provenance metadata. Field names match the implemented metadata schema defined in ADR-003 and `platform/knowledge/schema/asset-metadata-schema.yaml`.

| Field | Description | Required |
|---|---|---|
| `id` | Unique knowledge asset identifier (`KA-NNN`) | Yes |
| `title` | Human-readable title | Yes |
| `status` | `draft` \| `active` \| `review` \| `deprecated` \| `archived` | Yes |
| `created` | ISO 8601 date on which the asset was created (`YYYY-MM-DD`) | Yes |
| `updated` | ISO 8601 date of the last update (`YYYY-MM-DD`) | Yes |
| `author` | Operator ID or system component ID that created the asset | Yes |
| `origin` | Source: `manual`, workflow ID, or ingestion pipeline ID | Yes |
| `version` | Integer version counter; starts at 1, incremented on each update | Yes |
| `provenance.source_uri` | Original source URI if ingested from an external source | Yes |
| `provenance.ingested_via` | Ingestion pipeline identifier if produced by a pipeline | Yes |
| `tags` | Free-form tags for categorisation and filtering | Yes |
| `related` | IDs of related knowledge assets (`KA-NNN`) | Yes |
| `canonical` | Boolean — `true` for canonical assets, `false` for derived | Recommended |
| `reviewed_by` | Operator ID who reviewed this asset (required for canonical active assets) | If canonical |
| `reviewed_at` | Date of the review that transitioned the asset to `active` | If canonical |
| `derived_from` | For derived assets: list of source asset IDs | If derived |
| `sensitivity` | `low` \| `medium` \| `high` | Recommended |
| `retention_policy` | Retention period or rule | Recommended |

---

## Knowledge lifecycle

```
Draft → Active → Review → Deprecated → Archived
              ↑                ↓
              └── (promoted back if revised)
```

| State | Description | Transition trigger |
|---|---|---|
| Draft | Being authored; not yet ready for use | Initial creation |
| Active | Reviewed and available for use | Human review and approval |
| Review | Scheduled for periodic review; may still be used | Review cadence or trigger |
| Deprecated | Superseded or no longer recommended | Operator decision or new version |
| Archived | Retained for historical reference only; not for active use | Operator decision |

Lifecycle transitions are logged with timestamp, operator ID, and reason.

---

## Retrieval and indexing intent

The knowledge retrieval approach is intentionally layered:

1. **Identifier-based retrieval** — direct lookup by ID or file path. Always available. No AI required.
2. **Metadata-filtered retrieval** — filter by status, category, tags, date range. Available from Phase 3.
3. **Full-text search** — keyword search over canonical text. Available from Phase 3.
4. **Semantic search** — embedding-based similarity search using derived embeddings. Available from Phase 4 or later.

Semantic search is derived from canonical content. It supplements but does not replace identifier-based and metadata-filtered retrieval.

---

## Quality expectations

| Expectation | Description |
|---|---|
| Completeness | Required metadata fields are present |
| Accuracy | Content is factually correct; AI-generated content is human-verified before promotion |
| Currency | Review cadence is defined and followed; stale content is flagged |
| Provenance | Every asset has a traceable origin |
| Accessibility | Assets are retrievable by authorised queries |

Quality is reviewed as part of the Knowledge Governance domain defined in [`governance/governance-model.md`](../governance/governance-model.md).

---

## Relationship to workflows and memory

- **Workflows** consume canonical knowledge assets as inputs. They may produce derived knowledge as outputs.
- **Working memory** is derived and scoped to an active task or session. It does not replace canonical knowledge.
- **Provenance chains** link workflow outputs back to their source knowledge assets.
- AI model calls that use knowledge assets record the asset ID(s) in the model gateway audit log.

---

## Backup and restore

- All canonical knowledge is backed up on a defined schedule.
- Backup procedures are documented and tested at Phase 3 exit.
- Derived assets may be excluded from backup where they are regenerable.
- Restore procedures produce a verifiable canonical state.

---

## Related artifacts

- [`ontology/minimal-viable-ontology.md`](../ontology/minimal-viable-ontology.md) — ontology that governs knowledge entity types
- [`governance/governance-model.md`](../governance/governance-model.md) — Knowledge Governance domain
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — DOC IDs used for knowledge assets
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-001 (Knowledge Management)
