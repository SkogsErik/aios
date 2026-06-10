# Pivot Readiness Assessment

**ID:** DOC-018
**Status:** Active
**Last reviewed:** 2026-06-10
**Parent:** VIS-001
**Related:** DOC-016, DOC-017, DOC-002, DOC-003, DOC-004, DOC-005, DOC-008

---

## Purpose

This document is an independent architectural review of the AIOS repository at the point of its identity-centric pivot. It assesses the quality, completeness, and internal consistency of the pivot analysis (DOC-016, DOC-017), identifies gaps not addressed in those documents, and makes concrete recommendations for the next phase of work.

It is intended as a peer review artefact to support the team's decision-making. It does not supersede DOC-016 or DOC-017 — it challenges and extends them.

---

## 1. Strengths of the Existing Work

Before addressing gaps, the following should be stated plainly: the AIOS repository represents an unusually disciplined approach for a personal platform project.

| Strength | Assessment |
|---|---|
| Architecture-first discipline | Maintained consistently through Phases 1–4. Every implementation decision is traceable to a documented intent. |
| Self-critical analysis | DOC-017's critique of DOC-016 demonstrates genuine intellectual rigor. Identifying "storage-first thinking" as the unconscious inheritance of the original architecture is the kind of second-order analysis that most projects never produce. |
| Attention architecture (DOC-017 §4) | Cognitively grounded. Decay functions, capacity limits from Miller's Law, state transitions, and the attention dependency graph are all implementable and correct. |
| Project/Goal/FocusArea hierarchy | The Values → Goals → Focus Areas → Projects decomposition is the right abstraction stack for executive cognition. It correctly locates daily attention allocation at the project level, not the goal level. |
| Commitment as a distinct concept | Recognising that commitments carry social weight that goals do not — and modelling them separately — is a non-obvious but important architectural decision. |
| Governance foundation | The combination of ADR process, autonomy maturity model, and traceability standard is more rigorous than most production systems. |

---

## 2. Critical Gaps

### Gap A — The Pivot Has No ADRs (Governance Violation)

Both DOC-016 and DOC-017 close with the statement "this is an analysis, not a decision." That framing is correct for an analysis document. The problem is that no decision has followed.

The identity-centric pivot is the most significant architectural change in the project's history. It affects:
- The identity model (ADR-004 is explicitly marked for supersession in DOC-016)
- The knowledge architecture (DOC-009 must be extended for experiential data)
- The runtime model (ADR-005 selected CLI-invocation; continuous operation requires a new decision)
- The capability map (DOC-005 has no capabilities for identity, persona, or executive cognition)
- The target architecture (DOC-004 layers 2, 4, and 6 are extended but not formally revised)

**The pivot exists in analysis documents that are not referenced by the official architecture.** Until the pivot produces ADRs, the capability map, roadmap, and principles documents describe a different system from the one being designed. This is the definition of architectural drift — the risk the traceability standard was built to prevent.

**Minimum ADRs required to formalise the pivot:**

| ADR | Decision | Supersedes |
|---|---|---|
| ADR-007 | Identity as a persistent domain object (Persona, not session credential) | ADR-004 |
| ADR-008 | Observation store architecture (schema, storage, capture mechanism) | — |
| ADR-009 | Executive reasoning engine pattern (deterministic vs AI-assisted layers) | — |
| ADR-010 | Runtime model evolution (from CLI-invocation to persistent daemon) | ADR-005 (partial) |

Without these, no implementation work on the pivot is traceable to the governance baseline.

---

### Gap B — Silent Naming Collision: PROJ vs PRJ

The traceability standard (DOC-008) now contains two different entities named "Project":

| Prefix | Defined in | Meaning |
|---|---|---|
| `PROJ` | Original ontology (DOC-010), traceability standard | A bounded unit of platform delivery work |
| `PRJ` | DOC-017, traceability standard | An operator-level productivity unit with attention, health, and momentum |

These are genuinely different concepts with different schemas, different lifecycles, and different roles in the system. The collision is not a naming accident — it reflects a real architectural question: does the system have one project concept or two?

**Options:**
1. **Merge** — extend `PROJ` to carry both delivery and personal-productivity semantics. Risk: overloaded concept that is confusing in governance contexts.
2. **Separate explicitly** — rename one (e.g., `DPROJ` for delivery project, `PRJ` for personal project) and document the distinction clearly.
3. **Deprecate PROJ** — treat personal projects (`PRJ`) as the universal concept and model platform delivery work as a subtype.

This requires a decision (ADR) before either concept is implemented. Building data stores around ambiguous identifiers compounds technical debt rapidly.

---

### Gap C — Observation Capture Is Unsolved and Is the Hardest Problem

The entire identity, persona, and executive reasoning system depends on a continuous stream of high-quality observations. Every component of DOC-017's architecture — attention decay, preference learning, habit detection, decision modeling, reflection cycles — requires observations as input.

DOC-016 proposes "add an `observations/` directory, schema, CLI; wire workflow runtime to auto-record." This treats observation capture as a storage problem. It is not. It is a **behaviour change problem**.

The failure mode is well-understood from prior personal knowledge management systems (PKM, Roam, Obsidian, Day One): tools that require deliberate logging produce sparse, irregular, high-quality-but-low-volume data. Tools that passively capture produce dense, low-quality data. Neither alone is sufficient.

**What the architecture does not yet address:**

| Question | Status |
|---|---|
| How are observations generated passively? | Not designed |
| What is the minimum friction for manual observation capture? | Not designed |
| What external signals feed the observation stream (calendar, git, files)? | Mentioned as inputs in DOC-017 §3 but not architecturally designed |
| What is the quality threshold for an observation to be useful? | Not defined |
| How are duplicate/redundant observations deduplicated? | Not addressed |
| What is the retention policy for raw observations? | Not addressed |

Without a credible observation capture strategy, the identity model is a schema with no data. This should be the highest-priority design problem after the ADR backlog is closed.

---

### Gap D — The Implementation Gap Is a Discontinuity, Not an Increment

The current platform implementation rests on a specific set of architectural choices:

```
subprocess.run(command, shell=True)     # workflow execution
JSONL append                             # audit trail
YAML file with provenance metadata       # knowledge store
litellm.completion()                     # model call
```

DOC-017's target system requires:

```
Continuous daemon with event loop        # attention manager
Decay function scheduler                 # per-item attention computation
Real-time signal detection               # across multiple stores simultaneously
Multi-cycle reflection engine            # daily/weekly/monthly/quarterly triggers
Dynamic priority computation             # over a live project/commitment graph
```

These are not the same architecture. The gap between them is not bridgeable by adding Python modules to the existing workflow runtime. It requires:

1. A persistent process model (daemon, not CLI)
2. A state persistence layer that survives process restarts
3. An event loop or scheduler that operates independently of operator invocations
4. Cross-store query capability (attention manager must read projects, commitments, observations, and goals simultaneously)

**The "Incremental Evolution" framing in DOC-016 is optimistic to the point of being misleading.** Step 4 (background scheduler) alone requires superseding ADR-005 and redesigning the runtime model. This should be stated plainly rather than framed as a low-complexity additive step.

Recommended reframing: the identity/executive layer is a **new runtime** that co-exists with the existing workflow runtime rather than extending it. The existing YAML workflow executor handles governed, traceable, discrete tasks. The executive layer handles continuous state management. They share the model gateway and knowledge store but are otherwise separate subsystems.

---

### Gap E — Continuous Operation Transition Requires an ADR

ADR-005 explicitly chose "CLI invocation" and called out "no scheduler, no server, no daemon" as a feature. That was the right call for Phase 4.

The executive reasoning engine described in DOC-017 cannot run as a CLI tool. It requires a persistent process. This is a fundamental architectural transition:

| Dimension | Current (ADR-005) | Required for DOC-017 |
|---|---|---|
| Process model | Invoke and exit | Persistent daemon |
| State | Loaded fresh per invocation | Persistent across invocations |
| Triggers | Operator command | Time, events, patterns |
| Concurrency | None | Multiple concurrent state machines |
| Failure model | Exit code | Crash recovery, state restoration |

A new ADR should explicitly supersede the "no daemon" constraint of ADR-005 for the executive layer while preserving the CLI executor for governed workflow execution.

---

### Gap F — Personal Data Governance Is Absent

The Persona model described in DOC-016 and DOC-017 stores:

- Values, beliefs, and habit patterns
- Decision history with context and rationale
- Relationship models (connections to people and organisations)
- Energy levels and behavioral patterns across time
- Preference profiles derived from observed behavior

This is among the most sensitive personal data possible. The governance model (DOC-006) has five governance domains: Architecture, Knowledge, AI/Model, Autonomy, Operational. None covers personal data.

**Questions that require governance answers before implementation:**

| Question | Why it matters |
|---|---|
| What is the retention policy for observations and persona data? | Without a policy, data accumulates indefinitely; stale data degrades inference quality |
| What service identities (ADR-004) have read access to the persona? | The workflow runtime, reflection engine, and attention manager all need access; scope must be bounded |
| What is the threat model for observation store compromise? | Local-first reduces risk but doesn't eliminate it; the sensitivity of this data warrants explicit threat modeling |
| Can persona data be exported or deleted cleanly? | Important for operator autonomy and potential platform migration |
| How is AI-generated persona inference (habits, preferences) distinguished from operator-declared persona facts? | Analogous to the canonical/derived split already established for knowledge assets — needs the same treatment |

The canonical/derived split that governs knowledge assets (DOC-009, Principle 7) should be applied to persona data: operator-declared facts are canonical; AI-inferred patterns are derived. This needs to be formally stated.

---

### Gap G — The Deterministic/AI Boundary Is Undrawn

DOC-017's executive reasoning engine conflates two different classes of computation that have very different implementation timelines, reliability profiles, and governance requirements:

**Deterministic computation** (implementable now, reliable, no AI required):
- Attention decay functions
- Deadline proximity scoring
- Stall detection (days without attention)
- Commitment urgency ranking
- Fragmentation alerts (active item count > 3)
- Dependency graph traversal

**AI-assisted reasoning** (requires working model + quality evaluation):
- Pattern detection in observation streams ("you usually do X before Y")
- Decision context assembly ("your past pattern suggests option A")
- Preference learning from behavioral data
- Insight extraction from reflection cycles
- Anomaly detection ("this behavior is unusual for you")

The architecture should explicitly model these as **two layers**:

```
Layer 1 (Rules Engine): Deterministic, always-on, no model dependency
  → Produces: attention budgets, stall alerts, deadline warnings, fragmentation notices

Layer 2 (AI Reasoning): Model-dependent, triggered on schedule or threshold
  → Produces: patterns, decision context, preference suggestions, insights
  → Always requires human review before influencing persona
```

The rules engine can be built and deliver value immediately. The AI reasoning layer can be introduced under the existing autonomy maturity model controls. This also makes the system more resilient: executive function degrades gracefully if the model is unavailable rather than failing completely.

---

### Gap H — Roadmap Is Stale Relative to the Vision

The official roadmap (DOC-002) describes:

| Phase | Title |
|---|---|
| Phase 5 | Human-in-the-Loop Assistance |
| Phase 6 | Delivery Integration |
| Phase 7 | Controlled Autonomy |

None of these phases mentions identity platform, persona model, observation store, goal model, executive reasoning engine, attention manager, or reflection engine. The pivot described in DOC-016 and DOC-017 represents a fundamental revision of the post-Phase 4 roadmap.

Operating with a stated roadmap and an actual intention that are inconsistent undermines the traceability principle (DOC-003, Principle 5). The roadmap should either be revised to reflect the pivot, or the analysis documents should be explicitly marked as not-yet-adopted proposals.

**Recommended action:** A roadmap revision ADR that explicitly replaces Phases 5–7 with an identity-first sequence, retaining the original phases as options to be revisited once the identity foundation is operational.

---

## 3. Recommended Next Actions (Priority-Ordered)

### Immediate (close the governance gap)

| Priority | Action | Rationale |
|---|---|---|
| 1 | Author ADR-007: Identity as Domain Object | Supersedes ADR-004; formalises the pivot's most foundational decision |
| 2 | Author ADR-008: Observation Store Architecture | Unblocks all persona/learning work; must address capture mechanism, not just storage |
| 3 | Resolve PROJ vs PRJ naming collision | A confusing identifier collision that will compound with every document written from now |
| 4 | Revise roadmap (DOC-002) or formally adopt the pivot | Eliminates the inconsistency between stated direction and actual intention |

### Near-term (unblock implementation)

| Priority | Action | Rationale |
|---|---|---|
| 5 | Author ADR-009: Executive Reasoning Engine Pattern | Defines the deterministic/AI boundary and the runtime architecture |
| 6 | Author ADR-010: Runtime Model Evolution | Explicitly supersedes the "no daemon" constraint; required before any continuous operation work begins |
| 7 | Draft personal data governance domain | Extends DOC-006 with a sixth domain; analogous canonical/derived split for persona data |

### Strategic (before major implementation)

| Priority | Action | Rationale |
|---|---|---|
| 8 | Design observation capture strategy | Solves the hardest problem in the identity system before building storage for data that may never arrive |
| 9 | Prototype the deterministic rules engine | Delivers immediate value (stall detection, deadline warnings, fragmentation alerts) without waiting for the AI reasoning layer |
| 10 | Update DOC-004 and DOC-005 | Target architecture and capability map should reflect the identity-centric pivot's new layers and capabilities |

---

## 4. On the Risk of Documentation Paralysis

One risk deserves direct acknowledgment: the sophistication of this project's documentation practice creates its own danger.

DOC-016 and DOC-017 are detailed, well-structured, and intellectually rigorous. They are also both in an indefinite "analysis, not decision" state. The risk is that the project produces high-quality analysis faster than it adopts decisions, and decisions are adopted faster than they produce implementation.

The governance framework exists to prevent implementation from outrunning intent. It should not become a mechanism by which intent never reaches implementation.

A useful heuristic: if more than two analysis documents exist in `architecture/` that have no corresponding ADRs, governance overhead has exceeded implementation bandwidth. The current count is two (DOC-016, DOC-017). The next document in this folder should be an ADR, not another analysis.

---

## 5. Summary Assessment

| Dimension | Assessment | Verdict |
|---|---|---|
| Architecture foundation (Phases 1–4) | Solid, well-governed, internally consistent | ✅ Strong |
| Pivot identification (DOC-016) | Correct diagnosis; gaps identified accurately | ✅ Good |
| Pivot deepening (DOC-017) | Best analytical work in the repo; cognitively grounded | ✅ Strong |
| Pivot formalisation | Zero ADRs; no official architecture changes | ❌ Missing |
| Roadmap alignment | Officially points to Phases 5–7 that the pivot makes obsolete | ❌ Stale |
| Observation capture strategy | Not designed; existential risk to the identity model | ⚠ Critical gap |
| Implementation gap assessment | Underestimated in DOC-016; discontinuity not acknowledged | ⚠ Needs correction |
| Personal data governance | Absent; most sensitive data in the system has no governance domain | ⚠ Required before implementation |
| PROJ/PRJ naming | Active collision in traceability standard | ⚠ Fix now |
| Deterministic/AI boundary | Not drawn; conflated in DOC-017 | ⚠ Needs explicit separation |

The AIOS project has the right vision, the right analytical tools, and a sound foundation. What it needs now is fewer analyses and more decisions.

---

## Related Artifacts

- [DOC-001 — Vision](../docs/vision.md)
- [DOC-002 — Roadmap](../docs/roadmap.md)
- [DOC-003 — Architecture Principles](architecture/principles.md)
- [DOC-004 — Target Architecture](architecture/target-architecture.md)
- [DOC-005 — Capability Map](architecture/capability-map.md)
- [DOC-006 — Governance Model](../governance/governance-model.md)
- [DOC-008 — Traceability Standard](../governance/traceability-standard.md)
- [DOC-009 — Knowledge Architecture](../knowledge/knowledge-architecture.md)
- [DOC-016 — Identity-Centric Pivot Analysis](identity-centric-pivot-analysis.md)
- [DOC-017 — Executive Cognition Analysis](executive-cognition-analysis.md)
- [ADR-004 — Identity Model](../adr/0004-identity-model.md)
- [ADR-005 — Workflow Engine Technology](../adr/0005-workflow-engine-technology.md)
