# Identity-Centric Pivot Analysis

**ID:** DOC-016
**Status:** Active
**Last reviewed:** 2026-06-10
**Parent:** VIS-001

---

## Purpose

This document assesses the current AIOS architecture against a reframed vision: AIOS as a personal cognitive extension and digital executive assistant that evolves into a personalized model of its owner — not a generic agent framework.

It identifies gaps, proposes conceptual additions, and outlines an incremental evolution path that preserves existing investment while shifting the center of gravity toward identity, learning, and persistent personal context.

---

## Motivation

The existing architecture (DOC-003, DOC-004, DOC-005) was designed around governed capability delivery: the system's purpose is to implement traceable capabilities through bounded workflows. This produced a well-structured foundation, but the center of gravity is platform capabilities rather than the user.

The reframed vision asks a different question: not "what can the system do?" but "how well does the system know its operator?" This shifts the priority from capability traceability to identity fidelity — from documenting what was built to representing who the operator is.

---

## 1. Current Architecture Assessment

### What AIOS currently optimizes for

Governed capability delivery through document-driven orchestration. The deep ordering principle is:

```
Vision -> Theme -> Capability -> Workflow -> Knowledge Asset -> ADR
```

Every artefact traces upward to a capability definition. Every decision is documented. Every workflow is bounded and auditable. The architecture is organized around what the system can do and how its correctness is proven.

### Embedded assumptions

| Assumption | Evidence | Implication for pivot |
|---|---|---|
| Knowledge = curated documents | Knowledge platform stores Markdown files with YAML front-matter. Five knowledge categories defined; none for personal history or user model. | No category for experiential or observational data. |
| Traceability = capability hierarchy | Traceability chain: Vision -> Theme -> Capability -> Solution -> Project -> Repository -> Implementation. The user is absent. | No way to trace a decision back to operator intent or values. |
| AI assistance = reactive CLI calls | Model gateway has a `complete()` function invoked only by workflows or CLI commands. No event loop, scheduler, or background process. | No proactive behaviour, no continuous operation. |
| Identity = service account | ADR-004 defines operator identity as a session credential for auth. No persistent identity across sessions. | Every interaction starts from zero context. |
| Memory = provenance metadata | CAP-009 (Memory and Provenance) tracks document lineage, not personal experience. | System remembers what files say, not what the operator did. |
| Working memory = transient | Knowledge architecture classifies working memory as derived and non-canonical. | Task context is explicitly disposable; continuity is not designed for. |
| Autonomy = permitted actions | Autonomy maturity model frames autonomy in terms of allowed behaviours, not representation fidelity. | No vocabulary for "how well the system represents the operator." |

### Current center of gravity

The centre of gravity is **capability traceability** embodied in the capability map and ADR process. The implementation (knowledge store + model gateway + workflow runtime) serves this by:

1. Managing documents (knowledge platform)
2. Gating model access (model gateway)
3. Running sequential scripts with audit (workflow runtime)

This is an architecture-documentation system with a CLI skin — appropriate for Phases 1-4, but its deep structure pulls toward "governed enterprise platform" rather than "personal cognitive extension."

---

## 2. Vision Alignment Assessment

| Area | Existing support | Missing capabilities | Architectural blockers |
|---|---|---|---|
| **Persistent identity** | Basic session auth (ADR-004) | No persistent user model; no identity accumulation across sessions | Identity treated as auth context, not first-class domain entity |
| **Long-term memory** | Knowledge store with versioned documents, provenance tracking | No episodic memory, no personal timeline, no experiential record | Knowledge architecture assumes knowledge = curated documents |
| **Preference learning** | None | No observation mechanism, no preference schema, no learning loop | Architecture has no feedback loop — only processes commands |
| **Goal tracking** | Roadmap phases, capability definitions (project-level) | No personal goal model, no goal lifecycle, no progress tracking | Traceability chain ends at implementation, not personal outcomes |
| **Project awareness** | PROJ-xxx identifiers exist in traceability standard | No runtime project tracking, no awareness of current work | Architecture governs platform delivery, not operator activity |
| **Decision modeling** | ADRs capture architectural decisions | No personal decision model | ADRs cover platform only, not personal decisions |
| **Reflection** | Governance reviews, traceability validation | No personal reflection, no pattern analysis | No introspective capability for user patterns |
| **Proactive behaviour** | None | No scheduler, no background monitoring, no suggestion engine | Architecture is fundamentally reactive |
| **Continuous operation** | Tools are CLI-based; no daemon | No persistent process, no event loop | Runtime model is "invoke and exit" |

---

## 3. Gap Analysis (Ranked by Impact)

### Gap 1: No persistent identity model (critical)

The system cannot answer "who is the operator?" Identity authenticates a session but does not represent the person. There is no schema for personal attributes, relationship history, decision patterns, or behavioural history.

**Impact:** Every interaction is context-free. The system cannot learn, predict, or personalise.

### Gap 2: No observation loop (critical)

The system cannot see the operator. There is no mechanism to observe behaviour, capture decisions, or record context. Everything is pull-based.

**Impact:** Without observations there is no learning data. The system remains a tool to operate, not an assistant that knows its operator.

### Gap 3: Memory equals documents, not experience (high)

Memory (CAP-009) is about provenance chains on documents. There is no concept of episodic memory (what happened yesterday), semantic memory about the user (preferences, habits), or procedural memory (how the user typically does things).

**Impact:** The system remembers what files say but has no memory of what the operator has done, thought, or experienced.

### Gap 4: No goal or intent model (high)

The system knows what capabilities exist but not what the operator wants. It cannot answer "what is the operator trying to achieve?" and therefore cannot align assistance with purpose.

**Impact:** Assistance is generic, not purpose-aligned.

### Gap 5: Reactive architecture (high)

Every interaction begins with a CLI invocation or workflow trigger. Nothing runs continuously.

**Impact:** The system can never proactively suggest, remind, alert, or reflect.

### Gap 6: No preference, habit, or value schema (medium)

Nowhere in the ontology, knowledge architecture, or capabilities is there a concept of user preference, habit, or value.

**Impact:** Behaviours that should be automated (habits) require manual workflow definitions. Everything requires equal effort.

### Gap 7: Decision model covers only architecture (medium)

ADRs model platform decisions but not personal decisions. Personal choices have no formal capture mechanism.

**Impact:** The system accumulates no understanding of how the operator decides, which is precisely the long-term goal.

### Gap 8: Working memory is second-class (medium)

Working memory is explicitly defined as non-canonical and derived — intentionally disposable.

**Impact:** Every task starts with empty context. The system does not know what the operator was doing yesterday.

---

## 4. Evolution Strategy

**Principle:** Preserve everything that exists. Add new concepts as layers, not replacements.

### What to preserve unchanged

| Component | Rationale |
|---|---|
| Knowledge Platform | Excellent foundation for canonical knowledge; add experiential memory alongside it |
| Model Gateway | Correctly designed; new features consume it through the same interface |
| Workflow Runtime | Extend with background scheduling; execution model stays the same |
| ADR Process | Continue for platform decisions; personal decisions use a related but distinct pattern |
| Capability Map | Still the right way to scope platform capabilities; add new capabilities as needed |
| Traceability Standard | Extend the entity hierarchy to include user-facing entities |
| Autonomy Maturity Model | Add "representation fidelity" as a dimension alongside "allowed behaviour" |
| Governance Model | Add identity governance and personal data governance domains |

### Incremental evolution steps

#### Step 1: Identity as a domain object

Add a persistent identity store alongside the knowledge store using the same file-based pattern.

**Reuse:** Knowledge store patterns (Markdown + YAML front-matter, same CLI patterns, same backup/restore).
**Complexity:** Low — pure additive, approximately 80 lines of Python plus 1 schema file.

#### Step 2: Observation log

Add a timestamped observation capture mechanism. Observations are the raw material for learning: decisions made, actions taken, events observed, notes recorded.

**Reuse:** Knowledge store storage and indexing patterns; model gateway for AI-assisted enrichment.
**Complexity:** Low-medium — approximately 200 lines plus CLI extensions.

#### Step 3: Goal model

Add a goal schema with lifecycle and hierarchical decomposition.

**Reuse:** Same file/schema pattern; can be stored alongside knowledge assets.
**Complexity:** Medium — approximately 300 lines plus workflow integration.

#### Step 4: Background scheduler

Add a lightweight scheduler to the workflow runtime for proactive triggers.

**Reuse:** Workflow runtime executor for triggered actions; model gateway for generation.
**Complexity:** Medium — approximately 400 lines plus daemon management.

#### Step 5: Preference learning

Add explicit preference learning through observation aggregation and AI-assisted pattern suggestion, always requiring human approval before activation.

**Reuse:** Knowledge store for persistence; model gateway for pattern suggestion; workflow runtime for batch analysis.
**Complexity:** Medium-high — approximately 500 lines plus careful governance design.

---

## 5. New Core Concepts

The following should become first-class domain objects in the ontology:

| Entity | Prefix | Description | Why first-class |
|---|---|---|---|
| **Persona** | PRS | The persistent representation of the operator — facts, preferences, history, patterns | Root object for the entire pivot; identity must be the center |
| **Observation** | OBS | A timestamped record of something that happened | Raw material for all learning |
| **Goal** | GL | A desired outcome with a lifecycle | Personal analog of capabilities; expresses operator intent |
| **Decision** | DEC | A choice made, with context, options, rationale, and outcome | Personal analog of ADRs; captures how the operator decides |
| **Preference** | PRF | A learned or declared inclination | Output of learning; input to personalisation |
| **Belief** | BLF | A held position with confidence level | Tracks how operator understanding evolves over time |
| **Habit** | HBT | A recurring pattern of behaviour | Automation opportunity; routine behaviour to learn and assist |
| **Relationship** | REL | A connection to a person, project, organisation, or tool | Provides context for decisions and priorities |
| **Reflection** | RFL | A periodic analysis of observations, decisions, and outcomes | Mechanism for extracting insight from accumulated data |

---

## 6. Identity-Centric Target Architecture

### Entities and relationships

```
Persona (PRS-001)
├── Facts (semantic: operator preferences, values, attributes)
├── Preferences (PRF-xxx)
├── Beliefs (BLF-xxx)
├── Habits (HBT-xxx)
├── Relationships (REL-xxx)
│
├── Goals (GL-xxx)
│   └── Sub-goals
│       └── Evidence from Observations
│
├── Decisions (DEC-xxx)
│   ├── Context
│   ├── Options considered
│   ├── Rationale
│   └── Outcome
│
├── Observations (OBS-xxx)
│   ├── Timestamped events
│   ├── Actions taken
│   └── Notes recorded
│
└── Reflections (RFL-xxx)
    ├── Period summary
    ├── Pattern detected
    └── Learning extracted
```

### Data flow

```
                  Persona
              (accumulates)
             /              \
     Observation Log     Knowledge Store
     (what happened)     (what I know)
            |                    |
     Pattern Learner        Model Gateway
     (finds habits,         (AI access)
      preferences)               |
            |                    |
         Reflection <--- Workflow Runner
     (periodic analysis)    (actions)
```

### Layer impact

The 8-layer architecture (DOC-004) is preserved. Key changes:

- **Layer 2 (Identity):** Expands from session auth to persistent persona. Personal data policies added.
- **Layer 4 (Knowledge):** Extends from document store to include observation, goal, decision, preference, belief, habit, relationship, and reflection stores.
- **Layer 6 (Workflow Runtime):** Background scheduler added for proactive triggers.
- **Layer 8 (Experience):** New interfaces for observation capture, goal management, reflection review, and persona dashboard.

A new cross-cutting concern — **Personal Context** — flows through all layers above Layer 2. Every request carries not just an identity context (who authenticated) but a personal context (who is the person, what are they working on, what are their goals).

---

## 7. Updated Traceability Chains

Two chains coexist:

### Platform traceability (existing, unchanged)

```
Vision -> Theme -> Capability -> Solution -> Project -> Repository -> Implementation
```

### Personal traceability (new)

```
Persona -> Goal -> Decision -> Observation -> Reflection
```

They connect where a personal decision leads to a platform change (Decision -> new ADR, new Capability, new Workflow).

---

## 8. Roadmap

### Next 30 days — highest leverage

| Week | Change | Complexity | Description |
|---|---|---|---|
| 1-2 | Identity as domain object | Low | Add `identity/` directory, persona schema, CLI; register PRS-001 |
| 2-3 | Observation capture | Low | Add `observations/` directory, schema, CLI; wire workflow runtime to auto-record |
| 3-4 | Goal model | Low-Medium | Add `goals/` directory, schema, CLI; define initial goals from pivot |

### Next 90 days — medium-term

| Month | Change | Complexity | Description |
|---|---|---|---|
| 2 | Background scheduler | Medium | Add daemon mode to workflow runtime; daily summary and goal check-in workflows |
| 2-3 | Reflection engine | Medium | Add reflection schema; monthly AI-assisted pattern analysis; review CLI |
| 3 | Preference system | Medium-High | Add preference schema; suggestion workflow; review and approval CLI |

### Long-term

| Horizon | Capability | Description |
|---|---|---|
| Year 1 | Identity + memory + goals + reflection | System knows the operator, remembers context, tracks goals, reflects on patterns |
| Year 2 | Preference learning matures | Habits detected; "What would the operator likely do?" for routine decisions |
| Year 3+ | Bounded representation | System represents the operator in pre-approved contexts with high fidelity |

---

## Related artifacts

- [DOC-001 — Vision](docs/vision.md) — vision document this analysis evaluates
- [DOC-003 — Architecture Principles](architecture/principles.md) — principles that shaped the current architecture
- [DOC-004 — Target Architecture](architecture/target-architecture.md) — 8-layer architecture extended by this analysis
- [DOC-005 — Capability Map](architecture/capability-map.md) — capabilities to be extended
- [DOC-008 — Traceability Standard](governance/traceability-standard.md) — identifier conventions for new entities
- [DOC-010 — Minimal Viable Ontology](ontology/minimal-viable-ontology.md) — ontology to be extended
- [ADR-004 — Identity Model](adr/0004-identity-model.md) — current identity decision, to be superseded by identity-as-domain-object ADR

---

## What this document does not do

This document is an analysis, not a decision. It identifies gaps and proposes directions. Each significant change described here requires its own ADR with documented context, options, rationale, and consequences — following the same governance process used for all architecture decisions in AIOS.
