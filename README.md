# AIOS — Personal AI Operating System

AIOS is a local-first Personal AI Operating System whose primary assets are governed knowledge, traceable decisions, and bounded AI workflows. Agents are a later runtime abstraction, not the foundation.

This repository is a combined **architecture + future implementation monorepo**, bootstrapped architecture-first so implementation can evolve from a clear, durable, and traceable foundation.

## Why architecture-first

AIOS is intended to become durable cognitive infrastructure for thinking, learning, planning, software development, research, and execution over many years — not a short-lived chatbot application. Starting with a governed architectural baseline ensures that every future implementation decision is traceable, every capability is deliberately bounded, and autonomy is introduced incrementally with appropriate controls.

## Guiding priorities

1. Architecture before implementation
2. Knowledge before agents
3. Governance before autonomy
4. Long-term maintainability over short-term productivity

## Repository structure

| Directory | Purpose |
|---|---|
| `docs/` | Vision, roadmap, and repository-level guidance |
| `architecture/` | Principles, capability map, and target architecture |
| `governance/` | Governance model, autonomy maturity, traceability, and policy artifacts |
| `knowledge/` | Knowledge architecture, taxonomy, and information management |
| `ontology/` | Minimal viable ontology and its planned evolution |
| `adr/` | Architecture Decision Records |
| `platform/` | Infrastructure and platform implementation (executive daemon, knowledge, model gateway) |
| `workflows/` | *(future)* Workflow definitions and operational playbooks |
| `agents/` | *(future)* Agent roles, policies, and evaluation artifacts |
| `experiments/` | Bounded experiments; do not define the platform by default |

Architecture, governance, knowledge, and ontology directories contain **governance artifacts only**. Platform, workflows, and agents directories are reserved for future implementation.

## Core architecture stance

AIOS is designed to be:

- **Local-first** — data and computation on the local system unless there is a compelling reason to go remote
- **Model-agnostic** — all model interaction flows through a governed gateway, never directly
- **Knowledge-centric** — structured, provenance-tracked knowledge is a first-class asset
- **Traceable end-to-end** — every decision, capability, and workflow traces to a documented intent
- **Incrementally autonomous** — autonomy is introduced stage by stage, with explicit controls at each stage
- **Simply founded** — complex orchestration is deferred until simple foundations are proven

## Quick start

Prerequisites: **Python 3.11+**, `git`, `pip3`

```bash
# 1. Clone and install dependencies
git clone https://github.com/SkogsErik/aios.git
cd aios
pip3 install --break-system-packages -r platform/executive-daemon/requirements.txt

# 2. Verify — all tests should pass
cd platform/executive-daemon
PYTHONPATH=src python3 -m pytest tests/test_project_store.py \
  tests/test_rules_engine.py tests/test_attention_manager.py \
  tests/test_learning_engine.py tests/test_pattern_detector.py \
  tests/test_stores.py -q
cd ../..

# 3. Initialise your persona
python3 platform/executive-daemon/src/cli.py persona init --name "Your Name"
python3 platform/executive-daemon/src/cli.py persona set-value "Deep work" --priority 1
python3 platform/executive-daemon/src/cli.py persona add-fact "I focus best in the morning" --category habit

# 4. Start the background daemon (watches git, runs every 5 minutes)
python3 platform/executive-daemon/src/cli.py start
python3 platform/executive-daemon/src/cli.py status

# 5. Add a project and a commitment
python3 platform/executive-daemon/src/cli.py project add "AIOS Phase 5" --weight 0.9
python3 platform/executive-daemon/src/cli.py commit add "Ship learning engine" \
  --deadline 2026-07-01 --project PRJ-001 --weight 0.8

# 6. Record an observation
python3 platform/executive-daemon/src/cli.py observe "Good focus session on the rules engine" \
  --energy high --project PRJ-001

# 7. Review patterns (after a few cycles)
python3 platform/executive-daemon/src/cli.py patterns
```

See [`platform/executive-daemon/README.md`](platform/executive-daemon/README.md) for the full CLI reference.



Complete the architecture baseline documented in `docs/roadmap.md`. The first milestone is a repository and documentation system capable of governing future platform decisions, knowledge growth, workflow automation, and controlled autonomy.

## Architecture documentation baseline

| Document | Location |
|---|---|
| Vision | [`docs/vision.md`](docs/vision.md) |
| Roadmap | [`docs/roadmap.md`](docs/roadmap.md) |
| Glossary | [`docs/glossary.md`](docs/glossary.md) |
| Architecture Principles | [`architecture/principles.md`](architecture/principles.md) |
| Target Architecture | [`architecture/target-architecture.md`](architecture/target-architecture.md) |
| Capability Map | [`architecture/capability-map.md`](architecture/capability-map.md) |
| Governance Model | [`governance/governance-model.md`](governance/governance-model.md) |
| Autonomy Maturity Model | [`governance/autonomy-maturity-model.md`](governance/autonomy-maturity-model.md) |
| Traceability Standard | [`governance/traceability-standard.md`](governance/traceability-standard.md) |
| Knowledge Architecture | [`knowledge/knowledge-architecture.md`](knowledge/knowledge-architecture.md) |
| Minimal Viable Ontology | [`ontology/minimal-viable-ontology.md`](ontology/minimal-viable-ontology.md) |
| ADR Process | [`adr/README.md`](adr/README.md) |
| Bootstrap ADR | [`adr/0001-bootstrap-repository-structure.md`](adr/0001-bootstrap-repository-structure.md) |
| Model Gateway ADR | [`adr/0002-model-gateway-pattern.md`](adr/0002-model-gateway-pattern.md) |
| Knowledge Persistence ADR | [`adr/0003-knowledge-persistence-approach.md`](adr/0003-knowledge-persistence-approach.md) |
| Identity Model ADR | [`adr/0004-identity-model.md`](adr/0004-identity-model.md) |
