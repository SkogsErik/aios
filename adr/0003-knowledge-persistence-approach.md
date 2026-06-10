# 0003 — Knowledge Persistence Approach

**ID:** ADR-003  
**Status:** Accepted  
**Date:** 2026-06-10  
**Affects:** CAP-001, CAP-009, THEME-002  
**Supersedes:** N/A  
**Superseded by:** N/A

---

## Context

AIOS requires a persistence layer for canonical knowledge assets. The knowledge platform (Layer 4) must support:

- Creation, update, versioning, and archival of knowledge assets
- Provenance metadata capture (origin, date, author, version, lineage)
- Lifecycle status tracking (draft → active → review → deprecated → archived)
- Retrieval by identifier, metadata filter, and eventually semantic query
- Backup and restore with no external service dependency
- Inspection and repair by a technically capable operator without specialist tooling

The platform is local-first and personal. There is one operator and no concurrent write scenarios at launch. The architecture must be simple enough to prove correct at Phase 3, extensible to support semantic search in later phases, and resilient against tooling lock-in.

---

## Decision

Use a **local file system store with structured metadata** as the primary persistence layer for the knowledge platform.

Each knowledge asset is stored as a Markdown file with a YAML front-matter block that carries provenance and lifecycle metadata. Assets are organised in a defined directory hierarchy. The file system provides versioning through the repository's version control (git). A structured index (a machine-readable YAML or JSON manifest) is maintained alongside the assets to support efficient lookup by identifier and metadata filter.

Semantic (vector) indexing is not implemented in Phase 3. It is explicitly deferred to a later phase and will be introduced via ADR when demonstrated need arises.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **File system + structured metadata (this decision)** | Fully local; inspectable with any text editor; version-controlled natively; no external dependencies; simple backup and restore; extensible | Manual index maintenance until tooling exists; no built-in semantic search; scales to ~tens of thousands of assets comfortably |
| **SQLite database** | Structured queries; fast lookup; single file for backup | Binary format — not directly human-inspectable; version-controlled diffs are opaque; requires SQLite tooling for repair; migrations introduce fragility |
| **Embedded vector database (e.g. Chroma, LanceDB)** | Semantic search from the start | Significant complexity for Phase 3; vector stores are less mature for document lifecycle management; harder to inspect and repair |
| **External managed database (PostgreSQL, etc.)** | Full relational capabilities; battle-tested | Violates local-first principle; introduces external service dependency; backup complexity; not appropriate for personal single-operator use |
| **Git repository as knowledge store** | Native versioning; familiar tooling | Git is not designed as a queryable knowledge store; metadata retrieval requires parsing; no lifecycle or provenance schema enforcement |

---

## Rationale

The file system approach satisfies all Phase 3 requirements and aligns with AIOS design principles:

- **Local-first.** No external services required. The entire knowledge store fits on a local disk and can be backed up with a simple file copy or `rsync`.
- **Inspectable.** Markdown files with YAML front-matter are readable and editable with any text editor. An operator can diagnose, repair, or migrate the knowledge store without specialist tooling.
- **Version-controlled.** Git provides a full history of every knowledge asset without additional infrastructure. Provenance of changes is captured automatically.
- **Simply founded.** The file system approach can be proven correct before adding complexity. Semantic indexing is deferred until workflows demonstrate an actual retrieval quality problem that requires it.
- **Extensible.** Adding a semantic index layer later is straightforward — it operates on the same asset files and does not require a migration of the primary store.

SQLite was the strongest alternative, offering better query performance and schema enforcement. It was rejected because binary diffs make it difficult to inspect changes in version control, and repair or migration without SQLite tooling introduces operational risk that is disproportionate to the scale of a personal knowledge platform.

The vector database approach was rejected for Phase 3 because it introduces complexity before simple retrieval is proven insufficient.

---

## Metadata schema

Every knowledge asset file must include a YAML front-matter block with the following fields:

```yaml
---
id: KA-NNN                    # Unique knowledge asset identifier
title: ""                     # Human-readable title
status: draft                 # draft | active | review | deprecated | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: ""                    # Operator or workflow that created the asset
origin: ""                    # Source: manual, workflow ID, ingestion pipeline ID
version: 1
provenance:
  source_uri: ""              # Original source URI if applicable
  ingested_via: ""            # Ingestion pipeline ID if applicable
tags: []
related: []                   # IDs of related knowledge assets
---
```

Additional metadata fields may be added as needed. All existing fields are preserved when new fields are added. Field removals require an ADR.

---

## Directory structure

```
knowledge/
  assets/
    <domain>/
      KA-NNN-short-title.md
  index/
    assets.yaml               # Machine-readable manifest: id, title, status, path, updated
  schema/
    asset-metadata-schema.yaml
```

Domain sub-directories are defined in the knowledge architecture. The index is regenerated by tooling on every write; it is not a primary source of truth.

---

## Consequences

**Positive:**
- Knowledge store is fully inspectable, repairable, and portable.
- No new infrastructure dependencies in Phase 3.
- Git history provides complete provenance of all changes.
- Backup is a solved problem (file copy, rsync, or git push to remote).
- Extensible to vector indexing without migrating the primary store.

**Negative:**
- No built-in semantic or full-text search in Phase 3; keyword and metadata-based retrieval only.
- Index consistency must be maintained by tooling; a corrupted index can be regenerated, but tooling must be reliable.
- File system performance degrades at very large scale (millions of assets); acceptable for personal use.

**Neutral:**
- Asset identifiers (`KA-NNN`) are assigned by ingestion tooling; the identifier namespace is managed in the traceability register.
- The metadata schema is version-controlled in `knowledge/schema/`; changes go through the ADR process.

---

## Risks

| Risk | Mitigation |
|---|---|
| Index and asset files diverge (partial write failure) | Index is always regenerable from asset files; tooling validates consistency at startup |
| Assets written outside the defined schema (missing required fields) | Schema validation at ingestion and on pre-commit hook; invalid assets are rejected, not silently accepted |
| Knowledge store grows too large for git-based versioning | Binary and large media assets are excluded from git; a threshold (e.g. 1 GB) triggers an ADR review of the storage strategy |
| Metadata schema evolves incompatibly | Schema versioning field in front-matter; migration tooling required before any breaking schema change |

---

## Related artifacts

- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — Layer 4 Knowledge Platform
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-001 Knowledge Management, CAP-009 Memory and Provenance
- [`knowledge/knowledge-architecture.md`](../knowledge/knowledge-architecture.md) — knowledge categories and lifecycle
- [`ontology/minimal-viable-ontology.md`](../ontology/minimal-viable-ontology.md) — KnowledgeAsset entity
