# 0012 — Wyrd Subsystem Boundary

**ID:** ADR-012
**Status:** Accepted
**Date:** 2026-06-11
**Affects:** CAP-011, CAP-012, CAP-014, CAP-015, CAP-016, THEME-004, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

Through Phase 5 and the early Phase 6 development sprint, a significant boundary problem has emerged in the executive daemon (`platform/executive-daemon/`). The module conflates two fundamentally different concerns:

**AIOS core** — the inference substrate:
- Event loop and daemon lifecycle (`daemon.py`)
- Deterministic rules engine (`rules_engine.py`)
- Attention decay manager (`attention_manager.py`)
- Five-stage learning/inference pipeline (`learning_engine.py`)
- Pattern detectors (`pattern_detector.py`)
- Raw persistence primitives (`stores.py`, `daemon_state.py`)

**Operator identity and understanding** — who the operator is and what they are doing:
- Persona store (`project_store.py` → `PersonaStore`)
- Project and commitment stores (`project_store.py` → `ProjectStore`, `CommitmentStore`)
- Observation capture sources (`capture/git_capture.py`)
- Declared facts, values, preferences
- Attention states for tracked items

These two concerns have **different rates of change**, **different trust models**, and **different governors**:

| Concern | Change driver | Trust basis | Governor |
|---|---|---|---|
| AIOS core | Engineering decisions | Code correctness, test coverage | Engineering discipline |
| Operator identity | Identity decisions | Operator intent | Operator review and approval |

As the system grows toward a review interface, calendar capture, and structured reasoning about the operator, the conflation will worsen. Capture sources, the review dialogue, and persona management will accumulate in the engineering substrate — making the boundary between "what the system does" and "what the system knows about you" increasingly opaque.

A second concern has also been articulated: **signal quality**. Not all observable data about an operator is equally meaningful. Behavioral telemetry (keystrokes, scroll, URL visits, app focus time) is high-volume, noisy, and privacy-invasive. It captures *what the operator did*, not *what they meant*. Structural intent signals — calendar commitments, declared priorities, reasoned decisions, kept and broken commitments — are low-volume, high-meaning, and directly operator-authored. The architecture must make this distinction explicit and govern it, not leave it implicit in the capture layer.

A name and a boundary are both needed.

---

## Decision

### Part 1: Introduce Wyrd as a named subsystem boundary

**Wyrd** is introduced as a named subsystem within the AIOS monorepo at `wyrd/`. It is not a separate repository. It is a domain boundary — an explicit architectural demarcation of everything the system knows *about the operator* versus everything the system *does as an engine*.

The name is deliberate. In Old Norse, *wyrd* (Old English: *wyrd*; Proto-Germanic: *wurdiz*) means fate, personal narrative, and the thread of a life. A subsystem that builds a persistent, evolving model of who an operator is deserves a name that carries that weight.

**Wyrd owns:**
- Persona (PRS) — declared facts, values, preferences, inferred attributes
- Projects (PRJ), commitments (CMT), goals (GL), focus areas (FCA)
- Observations (OBS) — the raw capture stream
- All capture sources — git, calendar, CLI, and future mechanisms
- The review interface — the operator's dialogue with derived inferences
- Schemas for all identity data entities
- All data stored under `platform/knowledge/persona/`, `platform/knowledge/projects/`, `platform/knowledge/commitments/`, `platform/knowledge/goals/`, `platform/knowledge/observations/`

**AIOS core (`platform/executive-daemon/`) owns:**
- Daemon event loop and process lifecycle
- Rules engine (deterministic, Layer 1)
- Attention manager (decay computation, state transitions)
- Learning engine (inference pipeline, Layer 2)
- Pattern detectors
- Raw store primitives for derived data (patterns, contradictions, predictions)
- Data stored under `platform/knowledge/daemon/`, `platform/knowledge/patterns/`, `platform/knowledge/contradictions/`, `platform/knowledge/predictions/`

**The shared interface between them is the filesystem.** Wyrd writes identity data to `platform/knowledge/`. AIOS core reads from the same paths. No programmatic API is defined between the two subsystems. The filesystem is the contract. This is consistent with ADR-003 (knowledge persistence approach) and ADR-010 (runtime model coexistence).

### Part 2: Define the signal quality principle

Wyrd explicitly governs signal quality at the capture layer. Two classes of input signal are recognised:

**Structural intent signals** — preferred:
- Calendar entries: explicit commitments of time, the scarcest personal resource
- Declared priorities: operator-stated ordering of projects, goals, and commitments
- Written observations: first-person statements about meaning, energy, and intent
- Commitment lifecycle: kept vs broken, which reveals revealed preference
- Reasoned decisions: declared choices with context and rationale

**Behavioral telemetry signals** — deprioritised at this stage:
- Keystroke cadence, scroll patterns, mouse activity
- Application focus time, URL visit history
- Idle detection, screen time analysis

Behavioral telemetry is not prohibited — it may become relevant at a later stage — but it is explicitly *not* the foundation of Wyrd's model of the operator. The foundation is structural intent. High-volume, noisy, privacy-invasive signals require a separate governance decision before introduction. This is a deliberate architectural choice, not a limitation.

### Part 3: Repository structure

```
aios/                               ← monorepo (REP-001)
│
├── platform/
│   ├── executive-daemon/           ← AIOS core: inference engines, daemon lifecycle
│   │   └── src/
│   │       ├── daemon.py
│   │       ├── rules_engine.py
│   │       ├── attention_manager.py
│   │       ├── learning_engine.py
│   │       ├── pattern_detector.py
│   │       ├── stores.py             ← derived data only (patterns, predictions)
│   │       ├── daemon_state.py
│   │       └── cli.py                ← delegates identity commands to wyrd/
│   │
│   ├── knowledge/                  ← shared data store (filesystem contract)
│   │   ├── persona/                ← owned by Wyrd, read by AIOS core
│   │   ├── observations/           ← owned by Wyrd, read by AIOS core
│   │   ├── projects/               ← owned by Wyrd, read by AIOS core
│   │   ├── commitments/            ← owned by Wyrd, read by AIOS core
│   │   ├── goals/                  ← owned by Wyrd, read by AIOS core
│   │   ├── patterns/               ← owned by AIOS core, surfaced via Wyrd review
│   │   └── daemon/                 ← owned by AIOS core
│   │
│   ├── model-gateway/
│   └── workflow-runtime/
│
└── wyrd/                           ← operator understanding subsystem
    ├── README.md
    ├── src/
    │   ├── project_store.py        ← moved from executive-daemon
    │   ├── goal_store.py           ← new
    │   ├── capture/
    │   │   ├── git_capture.py      ← moved from executive-daemon
    │   │   └── calendar_capture.py ← future (Phase 6)
    │   └── review/                 ← future (Phase 6): operator review dialogue
    ├── schema/                     ← moved from executive-daemon
    │   ├── project-schema.yaml
    │   ├── commitment-schema.yaml
    │   ├── persona-schema.yaml
    │   ├── goal-schema.yaml        ← new
    │   └── focus-area-schema.yaml  ← new
    └── tests/
```

### Part 4: Extraction policy

Wyrd remains in the AIOS monorepo until at least one of the following extraction triggers is met:

1. **Different deployment target** — Wyrd needs to run on a different platform (mobile, cloud) while AIOS core remains local
2. **Different contributors** — access separation between Wyrd and AIOS core becomes a governance requirement
3. **Different release cadence** — Wyrd ships independently on a schedule AIOS core cannot match
4. **Formal external consumers** — another system uses Wyrd data through a defined API

Until a trigger is met, extraction is premature. The monorepo boundary is sufficient and easier to evolve.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Named boundary in monorepo (this decision)** | Low risk; reversible; no invented API; follows established pattern; easy to extract later | Requires discipline to maintain boundary; no hard enforcement |
| **Separate `wyrd` repository immediately** | Hard boundary enforced by repo separation; separate release cycle | Requires inventing a stable API before the boundary is understood; merge-on-mistake is painful; premature abstraction |
| **Leave conflated in executive-daemon** | No immediate work | Boundary gets worse as calendar capture, review interface, and goal tracking accumulate; technical debt compounds |
| **New top-level `identity/` directory** | Neutral name | Does not capture the semantic weight of what the subsystem is; misses the opportunity for intentional naming |

---

## Rationale

The named boundary approach was chosen because:

- **Reversibility.** Monorepo → separate repos is a mechanical operation once the boundary is stable. The reverse is painful. Start with the low-risk option.
- **No premature API.** The filesystem contract (ADR-003) is already the interface. No new API surface needs to be designed or maintained.
- **The boundary exists conceptually.** The distinction between "inference engine" and "model of the operator" is already real. Making it structural makes it explicit and defensible.
- **Signal quality must be governed.** Without an explicit architectural decision, behavioral telemetry could be introduced incrementally without ever being challenged. This ADR establishes that structural intent is the foundation and behavioral telemetry requires a separate governance decision.
- **The name matters.** Wyrd communicates intent and weight in a way that `identity/` or `user-model/` do not. It will be used in documentation, ADRs, and eventually in user-facing surfaces. Choosing it deliberately now is worth the small cost.

---

## Consequences

**Positive:**
- The boundary between inference engine and operator model is explicit, documented, and enforced by directory structure.
- Capture sources (especially future calendar integration) have a clear home.
- The review interface (Phase 6) has a clear home.
- Signal quality is a first-class architectural concern, not an afterthought.
- Future extraction to a separate repository is straightforward.

**Negative:**
- The mechanical move of `project_store.py`, `schema/`, and `capture/` from `executive-daemon/` to `wyrd/` is required. Imports in `daemon.py` and `cli.py` must be updated. This is planned as the first Phase 6 implementation task.
- The directory boundary is enforced by convention, not by a hard technical barrier. Engineering discipline is required to maintain it.

**Neutral:**
- The filesystem contract between Wyrd and AIOS core is unchanged. Both continue to read from and write to `platform/knowledge/` subdirectories as today.
- No runtime changes in Phase 6 step 1 — this is purely a structural reorganisation.

---

## Related artifacts

- [ADR-003 — Knowledge Persistence Approach](0003-knowledge-persistence-approach.md) — the filesystem-as-contract pattern this ADR extends
- [ADR-007 — Identity as Domain Object](0007-identity-as-domain-object.md) — the identity pivot that made this boundary necessary
- [ADR-010 — Runtime Model Evolution](0010-runtime-model-evolution.md) — the two-runtime model that Wyrd coexists with
- [ADR-011 — Learning Architecture](0011-learning-architecture.md) — the inference pipeline that reads from Wyrd stores
- [DOC-016 — Identity-Centric Pivot Analysis](../architecture/identity-centric-pivot-analysis.md) — the analysis that identified the conflation risk
- [DOC-019 — Wyrd README](../wyrd/README.md) — the operational README for the Wyrd subsystem
- [`architecture/target-architecture.md`](../architecture/target-architecture.md) — updated to show Wyrd subsystem in Layer 2/4
- [`architecture/capability-map.md`](../architecture/capability-map.md) — CAP-016 added; CAP-011/012/014 annotated as Wyrd-domain
