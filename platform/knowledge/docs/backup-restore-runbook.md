# Backup and Restore Runbook

**ID:** DOC-012  
**Status:** Active  
**Last reviewed:** 2026-06-10  
**Parent:** CAP-001

---

## Purpose

Document the backup and restore procedures for the AIOS knowledge store. These procedures satisfy the Phase 3 exit criterion: "Backup and restore procedures are documented and tested."

---

## Prerequisites

- Python 3.10+ installed
- `platform/knowledge/requirements.txt` installed: `pip install -r requirements.txt`
- Working directory: the repository root or `platform/knowledge/`

---

## Backup procedure

### When to back up

- Before any large ingestion operation
- Before restoring from a previous backup
- On a defined schedule (recommended: daily, or at minimum before each significant workflow run)
- Before upgrading the platform tools

### Steps

1. Navigate to `platform/knowledge/`:

   ```bash
   cd platform/knowledge
   ```

2. Run the backup command:

   ```bash
   python src/cli.py backup
   ```

   By default, archives are created in `platform/knowledge/backups/`.

3. Optionally specify a custom destination:

   ```bash
   python src/cli.py backup --dest /path/to/external/backup/dir
   ```

4. Verify the output:

   ```
   Backup created: backups/knowledge-store-20260610T120000Z.tar.gz
   Checksum:       backups/knowledge-store-20260610T120000Z.tar.gz.sha256
   ```

5. The checksum file (`.sha256`) is created alongside the archive. Keep both files together.

### Offsite / remote backup

For additional resilience, copy the archive and checksum file to a separate location:

```bash
rsync -av platform/knowledge/backups/ /media/external-drive/aios-backups/
```

Or commit archives to a remote git repository if size permits (archives of text-only knowledge stores are typically small).

---

## Restore procedure

### When to restore

- After data corruption or accidental deletion
- When rolling back to a known-good state after a failed ingestion
- When migrating the knowledge store to a new machine

### Steps

1. **Identify the target archive.** Archives are in `platform/knowledge/backups/` (or wherever you directed them). They are named `knowledge-store-<timestamp>.tar.gz`.

2. Verify the archive integrity manually (optional, also done automatically by the restore command):

   ```bash
   sha256sum -c knowledge-store-20260610T120000Z.tar.gz.sha256
   ```

3. Navigate to `platform/knowledge/`:

   ```bash
   cd platform/knowledge
   ```

4. Run the restore command:

   ```bash
   python src/cli.py restore backups/knowledge-store-20260610T120000Z.tar.gz
   ```

   **Note:** The restore command automatically creates a pre-restore backup of the current store before overwriting anything. You will see:

   ```
   Pre-restore backup created: backups/knowledge-store-20260610T125500Z.tar.gz
   Restore complete. Store restored from: knowledge-store-20260610T120000Z.tar.gz
   ```

5. Verify the restore succeeded:

   ```bash
   python src/cli.py list
   python src/cli.py index rebuild
   ```

6. Confirm the expected assets are present and the index is consistent.

---

## Verifying backup integrity

To verify a backup archive without restoring it:

```bash
# Check the checksum
sha256sum -c knowledge-store-20260610T120000Z.tar.gz.sha256

# List the archive contents
tar -tzvf knowledge-store-20260610T120000Z.tar.gz
```

A healthy archive should contain:
- `store/assets/` — asset files organised by domain
- `store/index/assets.yaml` — the asset index

---

## Backup retention policy

| Archive type | Retention period |
|---|---|
| Daily backups | 30 days |
| Pre-restore backups | Indefinite (delete manually after confirming restore success) |
| Milestone backups (Phase transitions) | Indefinite |

Review and adjust the retention policy when storage constraints require it.

---

## Recovery from index corruption

If the index (`store/index/assets.yaml`) is corrupted or out of sync with asset files, rebuild it from the assets:

```bash
python src/cli.py index rebuild
```

The index is always regenerable from the asset files. Asset files are the source of truth; the index is derived.

---

## Related artifacts

- [ADR-003 — Knowledge Persistence Approach](../../../adr/0003-knowledge-persistence-approach.md) — defines backup as a first-class requirement
- [Knowledge Architecture](../../../knowledge/knowledge-architecture.md) — backup and restore section
- [Governance Model — Operational Governance](../../../governance/governance-model.md) — backup governance controls
