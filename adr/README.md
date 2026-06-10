# ADR Process

**Status:** Active  
**Last reviewed:** 2026-06-10

---

## What is an ADR?

An Architecture Decision Record (ADR) is a short document that captures a significant architectural decision: its context, the options considered, the decision made, its rationale, and its known consequences.

ADRs are the primary mechanism for making AIOS design decisions explicit, traceable, and revisable. They are not bureaucratic overhead — they are the durable record of *why* things are the way they are.

---

## When to create an ADR

Create an ADR whenever a decision:

- Affects the architecture, structure, or governance of the platform in a non-trivial way
- Selects a technology, pattern, or approach over alternatives
- Changes or supersedes a previous architectural decision
- Triggers an autonomy stage transition
- Establishes or changes a significant policy or standard
- Would be difficult or costly to reverse without a documented record

Do **not** create an ADR for:
- Routine implementation details that do not affect architecture
- Cosmetic or stylistic document changes
- Decisions that are trivially reversible and low-impact

When in doubt, create the ADR. It is cheaper than reconstructing the reasoning later.

---

## ADR structure

Every ADR follows this structure:

```markdown
# NNNN — Title

**ID:** ADR-NNN
**Status:** Proposed | Accepted | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Affects:** CAP-NNN, THEME-NNN (traceability references)
**Supersedes:** ADR-NNN (if applicable)
**Superseded by:** ADR-NNN (if applicable)

## Context

What situation, constraint, or requirement prompted this decision?

## Decision

What was decided?

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Option A | ... | ... |
| Option B | ... | ... |

## Rationale

Why was this option chosen over the alternatives?

## Consequences

What are the expected consequences — positive, negative, and neutral?

## Risks

What risks does this decision introduce or mitigate?

## Related artifacts

Links to relevant documents, capabilities, or other ADRs.
```

Not every section must be lengthy. An ADR may be concise as long as the decision, rationale, and consequences are clear.

---

## Status model

| Status | Meaning |
|---|---|
| Proposed | Draft under discussion; not yet in effect |
| Accepted | Decision is in effect and governs current design |
| Deprecated | Decision no longer applies; not replaced |
| Superseded | Decision replaced by a newer ADR (reference the replacement) |

Status is updated in the ADR header. Deprecated and superseded ADRs are retained for historical reference.

---

## Numbering convention

ADRs are numbered sequentially: `0001`, `0002`, `0003`, etc.

File names follow the pattern:

```
NNNN-short-title-with-hyphens.md
```

Example: `0001-bootstrap-repository-structure.md`

Numbers are never reused. If an ADR is superseded, the original file is retained with its number and marked `Superseded`.

---

## ADR register

| ADR | Title | Status |
|---|---|---|
| [ADR-001](0001-bootstrap-repository-structure.md) | Bootstrap Repository Structure | Accepted |

---

## Related artifacts

- [`governance/traceability-standard.md`](../governance/traceability-standard.md) — ADR-NNN identifier conventions
- [`governance/governance-model.md`](../governance/governance-model.md) — architecture governance domain
