# Workflow Runtime — Phase 4

**Capability:** CAP-004 (Workflow Orchestration)  
**Phase:** 4 — Runtime and Workflow Baseline  
**Status:** Active  
**Last reviewed:** 2026-06-10

---

## Purpose

This directory contains the Phase 4 implementation of the AIOS Workflow Runtime (Layer 6). It provides:

- **Execution** — run YAML-defined workflows step by step, with full audit logging
- **Audit** — every step execution is recorded in a structured run record
- **Approval gates** — workflows can declare human approval checkpoints before proceeding
- **Validation** — workflow definitions are validated before execution

Technology: custom Python executor with YAML workflow definitions, as decided in [ADR-005](../../adr/0005-workflow-engine-technology.md).

---

## Directory layout

```
platform/workflow-runtime/
  schema/
    workflow-schema.yaml          # Workflow definition schema
  src/
    executor.py                   # Core workflow executor
    run_log.py                    # Run record writer
    validator.py                  # Workflow definition validator
    cli.py                        # CLI: run, list, validate commands
  runs/
    WF-NNN-run-TIMESTAMP.yaml     # Run records (not committed)
  tests/
    conftest.py
    test_executor.py
    test_run_log.py
  docs/
    workflow-authoring-guide.md
  requirements.txt
```

---

## Installation

```bash
cd platform/workflow-runtime
pip install -r requirements.txt
```

---

## Usage

### Run a workflow

```bash
python src/cli.py run ../../workflows/WF-001-knowledge-ingest.yaml \
  --var source_file=/path/to/doc.md
```

### Validate a workflow definition

```bash
python src/cli.py validate ../../workflows/WF-001-knowledge-ingest.yaml
```

### List workflow run records

```bash
python src/cli.py runs list
python src/cli.py runs show WF-001-run-20260610T090000Z.yaml
```

---

## Workflow definition format

Workflows are YAML files in `workflows/`. Minimal example:

```yaml
id: WF-001
title: Example Workflow
version: 1
capability: CAP-001
description: A minimal example workflow.

inputs:
  - name: source_file
    description: Path to the source document.
    required: true

steps:
  - id: step-1
    name: List files
    command: "ls -la {source_file}"
    requires_approval: false

  - id: step-2
    name: Confirm ingestion
    command: >
      python platform/knowledge/src/cli.py ingest {source_file}
    requires_approval: false
```

Full schema: [`schema/workflow-schema.yaml`](schema/workflow-schema.yaml)

---

## Run record format

Every workflow execution produces a run record in `runs/`. Run records are YAML files with the following structure:

```yaml
run_id: WF-001-run-20260610T090000Z
workflow_id: WF-001
workflow_title: Example Workflow
started_at: "2026-06-10T09:00:00Z"
completed_at: "2026-06-10T09:00:05Z"
status: success   # success | failed | aborted
inputs:
  source_file: /path/to/doc.md
steps:
  - id: step-1
    name: List files
    started_at: "2026-06-10T09:00:00Z"
    completed_at: "2026-06-10T09:00:01Z"
    exit_code: 0
    status: success
    stdout: "..."
    stderr: ""
    approval_required: false
    approved_by: null
```

---

## Running tests

```bash
cd platform/workflow-runtime
python -m pytest tests/ -v
```

---

## Related artifacts

- [ADR-005 — Workflow Engine Technology Selection](../../adr/0005-workflow-engine-technology.md)
- [Capability Map — CAP-004](../../architecture/capability-map.md)
- [Workflow Definitions](../../workflows/)
- [Model Gateway](../model-gateway/)
