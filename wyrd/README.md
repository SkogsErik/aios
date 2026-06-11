# Wyrd — Operator Understanding Subsystem

**ID:** DOC-019  
**Status:** Active  
**Last reviewed:** 2026-06-11  
**Defined by:** ADR-012 (Wyrd Subsystem Boundary)

---

## What Wyrd is

Wyrd is the operator understanding layer of AIOS. It holds the persistent, evolving model of who the operator is — declared facts, values, preferences, projects, commitments, goals, and the observation stream that feeds the inference pipeline.

The name is deliberate. *Wyrd* (Old Norse) means fate, personal narrative, and the thread of a life. A subsystem that builds a genuine model of an operator's identity over time earns that name.

Wyrd is a **domain boundary within the AIOS monorepo** (`wyrd/`), not a separate system. AIOS core reads from Wyrd's stores through the shared filesystem contract (ADR-003). Wyrd is designed to be extractable as an independent repository once the boundary is stable and extraction triggers are met (see ADR-012).

---

## What Wyrd owns

| Entity | Store | Path |
|---|---|---|
| Persona (PRS-001) | `PersonaStore` | `platform/knowledge/persona/persona.yaml` |
| Projects (PRJ-NNN) | `ProjectStore` | `platform/knowledge/projects/PRJ-NNN.yaml` |
| Commitments (CMT-NNN) | `CommitmentStore` | `platform/knowledge/commitments/CMT-NNN.yaml` |
| Goals (GL-NNN) | `GoalStore` | `platform/knowledge/goals/GL-NNN.yaml` |
| Focus Areas (FCA-NNN) | `FocusAreaStore` | `platform/knowledge/focus-areas/FCA-NNN.yaml` |
| Observations (OBS-NNN) | append-only YAML | `platform/knowledge/observations/YYYY/MM/YYYY-MM-DD.yaml` |
| Git capture | `GitCapture` | reads repo, writes observations |

## What Wyrd does NOT own

- Daemon event loop and process lifecycle → `platform/executive-daemon/src/daemon.py`
- Rules engine, attention manager → `platform/executive-daemon/src/`
- Learning engine, pattern detectors → `platform/executive-daemon/src/`
- Derived data (patterns, contradictions, predictions) → `platform/knowledge/patterns/` etc.
- Conductor sessions → `platform/conductor/`

---

## Directory structure

```
wyrd/
├── README.md               ← this file
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── project_store.py    ← ProjectStore, CommitmentStore, PersonaStore
│   ├── goal_store.py       ← GoalStore, FocusAreaStore
│   └── capture/
│       ├── __init__.py
│       └── git_capture.py  ← automatic git observation capture
├── schema/
│   ├── project-schema.yaml
│   ├── commitment-schema.yaml
│   ├── persona-schema.yaml
│   ├── goal-schema.yaml
│   └── focus-area-schema.yaml
└── tests/
    ├── __init__.py
    ├── test_project_store.py
    └── test_goal_store.py
```

---

## Setup

```bash
pip3 install --break-system-packages -r wyrd/requirements.txt
```

---

## Running tests

```bash
# From the repo root
PYTHONPATH=wyrd/src:platform/executive-daemon/src python3 -m pytest wyrd/tests/ -q
```

---

## The signal quality principle

Wyrd is founded on **structural intent signals** — inputs that reflect deliberate operator commitments:
- Calendar entries (time commitments)
- Declared priorities and projects
- Written observations
- Kept and broken commitments

Behavioral telemetry (keystrokes, scroll, URLs) is explicitly deprioritised. High-volume, noisy signals are not the foundation of Wyrd's model. See ADR-012 for the full signal quality rationale.

---

## Related artifacts

- [ADR-012 — Wyrd Subsystem Boundary](../adr/0012-wyrd-subsystem-boundary.md)
- [ADR-007 — Identity as Domain Object](../adr/0007-identity-as-domain-object.md)
- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md)
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-011, CAP-012, CAP-014, CAP-016
