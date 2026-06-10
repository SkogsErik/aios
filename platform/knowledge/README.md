# Knowledge Platform — Phase 3

**Capability:** CAP-001 (Knowledge Management)  
**Phase:** 3 — Knowledge Baseline  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

This directory contains the Phase 3 implementation of the AIOS Knowledge Platform (Layer 4). It provides:

- **Ingestion** — ingest Markdown documents with YAML front-matter as versioned, provenance-tracked knowledge assets
- **Retrieval** — retrieve assets by ID, metadata filter, or full-text keyword search
- **Index management** — maintain a machine-readable manifest of all assets
- **Backup and restore** — back up the knowledge store and restore from an archive

The knowledge store uses a local file system with YAML front-matter metadata, as decided in [ADR-003](../../adr/0003-knowledge-persistence-approach.md).

---

## Store layout

```
store/
  assets/
    <domain>/
      KA-NNN-short-title.md   # Knowledge asset files
  index/
    assets.yaml               # Machine-readable manifest (rebuilt from assets)
```

Domains map to the knowledge categories defined in [`knowledge/knowledge-architecture.md`](../../knowledge/knowledge-architecture.md):

| Domain directory | Knowledge category |
|---|---|
| `general/` | Default; uncategorised assets |
| `architecture/` | Architecture and Governance Knowledge |
| `domain/` | Domain Knowledge |
| `operational/` | Operational Knowledge |

---

## Installation

```bash
cd platform/knowledge
pip install -r requirements.txt
```

---

## Usage

All commands are available through the `kn` CLI entry point.

### Ingest a document

```bash
python src/cli.py ingest <file.md> [--domain general] [--title "Title"] [--tags tag1,tag2]
```

Ingests a Markdown file into the knowledge store. If the file contains YAML front-matter, existing metadata is preserved and merged; required fields are added if absent.

### List assets

```bash
python src/cli.py list [--status active] [--domain general]
```

### Retrieve an asset

```bash
python src/cli.py get KA-001
```

### Search assets

```bash
python src/cli.py search "keyword phrase"
```

Full-text keyword search across asset content and metadata.

### Rebuild the index

```bash
python src/cli.py index rebuild
```

Regenerates `store/index/assets.yaml` from the asset files. Safe to run at any time.

### Backup the store

```bash
python src/cli.py backup [--dest ./backups]
```

Creates a timestamped `.tar.gz` archive of the store directory. See [`docs/backup-restore-runbook.md`](docs/backup-restore-runbook.md).

### Restore from backup

```bash
python src/cli.py restore <backup.tar.gz>
```

Restores the store from an archive. See [`docs/backup-restore-runbook.md`](docs/backup-restore-runbook.md).

---

## Metadata schema

Defined in [`schema/asset-metadata-schema.yaml`](schema/asset-metadata-schema.yaml). Required fields per ADR-003:

| Field | Description |
|---|---|
| `id` | Unique identifier (`KA-NNN`) |
| `title` | Human-readable title |
| `status` | `draft` \| `active` \| `review` \| `deprecated` \| `archived` |
| `created` | Creation date (`YYYY-MM-DD`) |
| `updated` | Last update date (`YYYY-MM-DD`) |
| `author` | Operator or workflow that created the asset |
| `origin` | Source: `manual`, workflow ID, or ingestion pipeline ID |
| `version` | Integer version counter (starts at 1) |
| `provenance.source_uri` | Original source URI (if applicable) |
| `provenance.ingested_via` | Ingestion pipeline ID (if applicable) |
| `tags` | List of tags |
| `related` | List of related asset IDs |

---

## Related artifacts

- [ADR-003 — Knowledge Persistence Approach](../../adr/0003-knowledge-persistence-approach.md)
- [Knowledge Architecture](../../knowledge/knowledge-architecture.md)
- [Capability Map — CAP-001](../../architecture/capability-map.md)
- [Backup and Restore Runbook](docs/backup-restore-runbook.md)
