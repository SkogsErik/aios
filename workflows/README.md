# Workflows

**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

This directory contains AIOS workflow definitions. Each workflow is a YAML file
that defines a bounded, governed sequence of operations.

Workflow definitions are governance artefacts. They are version-controlled here
and executed by the workflow runtime in `platform/workflow-runtime/`.

---

## Workflow register

| ID | Title | Capability | Status |
|---|---|---|---|
| [WF-001](WF-001-knowledge-ingest.yaml) | Knowledge Asset Ingestion | CAP-001 | Active |
| [WF-002](WF-002-knowledge-search.yaml) | Knowledge Store Search | CAP-001 | Active |

---

## Workflow definition format

See [`platform/workflow-runtime/schema/workflow-schema.yaml`](../platform/workflow-runtime/schema/workflow-schema.yaml) for the full schema.

Minimal example:

```yaml
id: WF-NNN
title: My Workflow
version: 1
capability: CAP-NNN

inputs:
  - name: my_var
    description: Description of the input.
    required: true

steps:
  - id: step-1
    name: Do something
    command: echo {my_var}
    requires_approval: false
```

---

## Running a workflow

```bash
cd platform/workflow-runtime
python src/cli.py run ../../workflows/WF-001-knowledge-ingest.yaml \
  --var source_file=/path/to/document.md \
  --var domain=general
```

Validate without executing:

```bash
python src/cli.py validate ../../workflows/WF-001-knowledge-ingest.yaml
```

---

## Related artifacts

- [ADR-005 — Workflow Engine Technology Selection](../adr/0005-workflow-engine-technology.md)
- [Workflow Runtime](../platform/workflow-runtime/)
- [Capability Map](../architecture/capability-map.md)
- [Traceability Standard](../governance/traceability-standard.md) — WF-NNN IDs
