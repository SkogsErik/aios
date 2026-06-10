# 0001 — Bootstrap Repository Structure

**ID:** ADR-001  
**Status:** Accepted  
**Date:** 2026-06-10  
**Affects:** VIS-001, THEME-001, REP-001  
**Supersedes:** N/A  
**Superseded by:** N/A

---

## Context

AIOS is a long-term Personal AI Operating System initiative. Before any implementation begins, the repository needs a structure that:

- Clearly separates architecture and governance artefacts from future implementation code
- Makes design intent traceable from high-level vision to specific decisions
- Can accommodate both documentation and implementation in a single monorepo without conflating them
- Establishes a governance foundation that governs all future evolution

At the time this ADR was written, the repository contained only a `README.md`. No directory structure, governance artefacts, or implementation code existed.

---

## Decision

Establish `SkogsErik/aios` as an **architecture-first monorepo** with explicit separation between:

1. **Architecture and governance artefacts** — `docs/`, `architecture/`, `governance/`, `knowledge/`, `ontology/`, `adr/`
2. **Future implementation areas** — `platform/`, `workflows/`, `agents/`, `experiments/`

The repository is bootstrapped with a complete documentation baseline (see deliverables in [`docs/roadmap.md`](../docs/roadmap.md)) before any implementation code is written.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Architecture-first monorepo (this decision) | Single source of truth; architecture governs implementation; traceability is structural | Requires discipline to maintain separation; governance overhead |
| Separate architecture and implementation repositories | Strong separation by default; implementation repos stay clean | Traceability across repos is harder; governance artefacts and code diverge over time |
| Implementation-first with documentation added later | Faster early velocity | Architecture debt accumulates; documentation often never catches up |
| No structure (ad hoc) | No overhead | Ungovernable at scale; no traceability; not appropriate for a long-term initiative |

---

## Rationale

The architecture-first monorepo approach best serves the long-term goals of AIOS:

- A single repository provides a unified traceability chain from vision to implementation.
- Starting with architecture artefacts establishes the foundation before implementation decisions accrue.
- Explicit directory separation maintains conceptual clarity without the operational overhead of multiple repositories.
- The approach allows governance artefacts to evolve in lockstep with implementation, reducing the risk of divergence.

The implementation-first approach was rejected because AIOS is explicitly designed to be a long-term, governance-first initiative. Starting with implementation before architecture is in place contradicts the core design priorities.

Separate repositories were rejected because they fragment traceability and increase the risk that architecture and implementation diverge silently.

---

## Consequences

**Positive:**
- Every implementation decision can be traced to a documented capability and principle.
- The repository communicates intent clearly to any future contributor or automated tool.
- The ADR process is active from day one, building a decision history over time.
- Governance artefacts and implementation evolve in the same version-controlled context.

**Negative:**
- The repository may appear to have no "runnable code" in its early phases. This is intentional.
- Maintaining separation between architecture and implementation directories requires ongoing discipline.
- Contributors must understand the governance model before making significant changes.

**Neutral:**
- The documentation baseline must be updated as the platform evolves; it is a living artefact, not a one-time deliverable.

---

## Risks

| Risk | Mitigation |
|---|---|
| Architecture artefacts become stale as implementation evolves | Traceability validation at each roadmap phase transition; periodic governance reviews |
| Boundary between architecture and implementation directories blurs over time | Clear directory conventions documented in `README.md`; ADR required for structural changes |
| Documentation overhead discourages contributions | Keep governance artefacts concise; prefer short, decision-focused ADRs over lengthy specifications |

---

## Related artifacts

- [`README.md`](../README.md) — repository overview implementing this structure
- [`docs/vision.md`](../docs/vision.md) — vision this structure serves
- [`docs/roadmap.md`](../docs/roadmap.md) — roadmap that delivers the documentation baseline
- [`governance/governance-model.md`](../governance/governance-model.md) — governance framework enabled by this structure
- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — traceability convention this structure supports
