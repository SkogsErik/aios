# 0007 — Identity as Domain Object

**ID:** ADR-007
**Status:** Accepted
**Date:** 2026-06-10
**Affects:** CAP-007, CAP-009, THEME-001, THEME-006
**Supersedes:** ADR-004
**Superseded by:** N/A

---

## Context

ADR-004 established a session-based identity model: the operator authenticates with a local credential, and the session carries a signed identity context for the duration of that session. Service identities are provisioned for platform components. This was the correct decision for Phase 4, where identity served authentication and audit attribution.

The identity-centric pivot (DOC-016, DOC-017) reframes AIOS as a personal cognitive extension. In this reframing, identity is not a session credential — it is the persistent representation of the operator that accumulates facts, preferences, history, and patterns over years. The session model from ADR-004 cannot support this because:

- **Session identity is ephemeral.** It exists only for the duration of a CLI invocation or login session. It carries no history, no preferences, no context from past sessions.

- **Session identity has no schema for personal data.** It models authentication (who is this?), not persona (who is this person? What do they value? How do they decide?).

- **Session identity provides no mechanism for learning.** The model has no feedback loop — identity data is static configuration, not an accumulating representation.

- **The executive reasoning engine (DOC-017) requires persistent identity.** Attention allocation, priority computation, decision support, and preference learning all depend on access to an accumulating model of the operator.

This ADR supersedes ADR-004's operator identity model while preserving its service identity model for platform component authentication.

---

## Decision

### Part 1: Persona as a first-class domain object

Introduce **Persona (PRS)** as a first-class domain object with its own store, lifecycle, and schema. The Persona is the persistent, accumulating representation of the operator.

The Persona store follows the same architectural pattern as the knowledge store (file-based, version-controlled, provenance-tracked) as established in ADR-003.

The Persona schema includes:

```yaml
# Schema: Persona entity
id: PRS-NNN              # Unique identifier
version: int              # Monotonically increasing
created: ISO8601          # Creation timestamp
updated: ISO8601          # Last update timestamp

# Core identity
name: string              # Operator's chosen name
declared_facts: []        # Operator-declared truths (canonical)
  - statement: string
    category: value | belief | preference | habit | constraint
    confidence: high | medium | low
    declared_at: ISO8601

# Inferred attributes (derived, from reflection/pattern analysis)
inferred_attributes: []
  - statement: string
    category: preference | belief | habit | pattern
    confidence: float (0-1)
    evidence: [OBS-NNN]   # Observations supporting this inference
    reviewed: bool         # Has operator reviewed this?
    promoted: bool         # Promoted to declared_fact after review

# Preferences
preferences: []
  - domain: string
    preference: string
    context: string        # When this preference applies
    source: declared | inferred
    confidence: float

# Values (slowest-changing layer)
values: []
  - value: string
    priority: int
    category: personal | professional | intellectual
    defined_at: ISO8601
    updated_at: ISO8601
```

### Part 2: Identity context expanded

The existing identity context (from ADR-004) is expanded to carry persona context:

```yaml
identity_context:
  # From ADR-004 (preserved)
  operator_id: operator-001
  session_id: session-uuid
  service_id: null | service-name

  # New: persona context
  persona_id: PRS-001
  persona_version: 42
  persona_facts: [summary of relevant facts]
  current_focus: PRJ-042     # Active project (from DOC-017)
  attention_state: focused | fragmented | idle
```

### Part 3: Service identity model preserved unchanged

The service identity component of ADR-004 (distinct service identities for platform components, least-privilege permissions, local secrets vault) is unaffected by this decision and remains in effect.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Persona as domain object + expanded identity context (this decision)** | Persistent; learnable; schema designed for both declared and inferred attributes; preserves service identities | Additional store to maintain; persona must be governed separately from knowledge assets |
| **Extend ADR-004 session model** | No new store; minimal change | Session model has no persistence mechanism; would require bolting accumulation onto an ephemeral foundation; architectural inconsistency |
| **Persona as knowledge assets** | Reuses existing knowledge store; no new infrastructure | Knowledge assets are designed for curated documents, not evolving identity models; conflates "what I know" with "who I am"; lifecycle mismatch |
| **Persona as database** | Structured queries; schema enforcement | Violates local-first inspectability principle; introduces binary dependency; contradicts ADR-003's file-based reasoning |

---

## Rationale

The Persona-as-domain-object approach was chosen because:

- **Persistence is not optional.** The entire pivot depends on identity accumulating over years. A session model cannot provide this.

- **Declared vs inferred separation is essential.** Following architecture Principle 7 (canonical vs derived data), operator-declared facts are canonical; AI-inferred patterns are derived and require human review before promotion. This maps cleanly to the existing knowledge architecture split.

- **File-based pattern is proven.** The knowledge store's Markdown + YAML front-matter pattern (ADR-003) is inspectable, version-controllable, and simple. Applying the same pattern to persona data is consistent and low-risk.

- **Service identities are independent.** The pivot changes the operator identity model but has no reason to change how platform components authenticate to each other. Preserving ADR-004's service identity model avoids unnecessary disruption.

---

## Consequences

**Positive:**
- The operator has a persistent identity that accumulates across sessions and years.
- Declared (canonical) and inferred (derived) persona attributes are explicitly separated, mirroring the knowledge architecture.
- The identity context now carries persona information that enables the executive reasoning engine (DOC-017) to operate.
- The file-based pattern is inspectable, portable, and consistent with the rest of AIOS.
- Service identities remain unchanged, preserving the existing authentication and audit trail infrastructure.

**Negative:**
- The persona store is an additional store to maintain, back up, and govern.
- Persona data is among the most sensitive in the system; existing governance domains (DOC-006) do not cover personal data (see DOC-018 Gap F).
- Migration path from ADR-004: existing session identity remains functional but does not automatically populate the persona store.

**Neutral:**
- The persona store sits alongside the knowledge store in Layer 4. They are separate stores with different schemas and lifecycles.
- Persona data governance is deferred to a domain-specific governance policy (recommended in DOC-018).

---

## Risks

| Risk | Mitigation |
|---|---|
| Persona store diverges from knowledge store patterns | Both stores follow ADR-003's file-based pattern; schema versioning and migration procedures apply to both |
| AI-inferred persona attributes promoted without review | Promotion requires explicit operator review; governed by the canonical/derived split (Principle 7) |
| Persona data accumulates stale attributes | Retention and decay policy defined in personal data governance (to follow) |
| Persona conflicts with existing knowledge schema | Persona is a separate store with separate schema; no conflict |

---

## Related artifacts

- [ADR-004 — Identity Model](0004-identity-model.md) — superseded by this ADR
- [ADR-003 — Knowledge Persistence Approach](0003-knowledge-persistence-approach.md) — pattern reused for persona store
- [DOC-016 — Identity-Centric Pivot Analysis](../architecture/identity-centric-pivot-analysis.md) — analysis this decision implements
- [DOC-017 — Executive Cognition Analysis](../architecture/executive-cognition-analysis.md) — analysis that requires this decision
- [DOC-018 — Pivot Readiness Assessment](../architecture/pivot-readiness-assessment.md) — peer review that identified this gap
- [DOC-006 — Governance Model](../governance/governance-model.md) — to be extended with personal data governance
- [Architecture Principle 7 — Canonical vs Derived](../architecture/principles.md) — applies to persona data
