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
| `platform/` | *(future)* Infrastructure and platform implementation |
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

## Near-term objective

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
