# 0011 — Learning Architecture

**ID:** ADR-011
**Status:** Accepted
**Date:** 2026-06-10
**Affects:** CAP-003, CAP-015, THEME-006, ADR-009
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

The identity-centric pivot (ADR-007 through ADR-010) establishes persistent storage for observations, persona attributes, projects, and commitments. These stores enable the system to *remember* — to recall what the operator said, did, and committed to.

DOC-009 (Learning Architecture Analysis) identifies a gap: remembering is insufficient for the system to function as a personal cognitive extension. The system must also *understand* — detect behavioral patterns, reconcile observed behavior against declared values, build confidence-weighted models of operator tendencies, and evolve those models through feedback.

The hard problem is not the stores. It is the **inference pipeline** and its governance: how does the system move from raw observations to high-confidence understanding without violating Principle 7 (canonical vs. derived)?

This ADR formalizes the learning architecture as a Layer 2 (AI reasoning) component of the executive reasoning engine (ADR-009), defining the inference pipeline, confidence model, feedback loops, store schemas, and governance boundaries.

---

## Decision

### Part 1: The inference pipeline is a five-stage scheduled process

The learning engine runs on a scheduled cadence (not continuous) as part of Layer 2 of the executive reasoning engine (ADR-009 Part 3). The five stages are:

**Stage 1 — Aggregation:** Raw observations are grouped into daily, weekly, monthly, and quarterly windows. Each window produces structured aggregates: time allocation, activity type breakdown, energy level distribution, decision outcomes, project velocity.

**Stage 2 — Pattern Detection:** Aggregations across consecutive windows are compared. Statistically significant deviations from expected baselines are flagged as candidate patterns.

**Stage 3 — Reconciliation:** Detected patterns are compared against the canonical persona. Divergence between declared values and observed behavior produces tensions.

**Stage 4 — Confidence Scoring:** Every detected pattern receives a deterministic confidence score (0.0–1.0) based on base rate, consistency, recency, specificity, and feedback history. Confidence scoring is a fixed function, not model-dependent.

**Stage 5 — Candidate Generation:** Patterns above the surface threshold (>= 0.4 confidence) are formatted as review candidates. Candidates below 0.4 are stored for model calibration but not surfaced.

### Part 2: All inferred patterns are derived until explicitly promoted

No inference automatically modifies the canonical persona. All pattern detection output is labelled as `derived` per Principle 7. Promotion to canonical requires explicit operator review and approval. This includes:

- Preference-behavior divergence patterns (they cannot adjust the preference weight)
- Behavioral bias patterns (they cannot adjust priority rankings)
- Energy correlation patterns (they cannot adjust scheduling)
- Rejection patterns (they cannot mute suggestion sources)

The only exception is confidence decay: patterns that the operator repeatedly rejects may be automatically archived after a configurable threshold (default: 3 rejections of the same pattern type within 30 days).

### Part 3: Confidence scoring is deterministic

Confidence is computed by a fixed formula, not by an AI model. This ensures that confidence scores are reproducible, auditable, and available without model dependency:

```
confidence = (0.3 × base_rate) + (0.3 × consistency) + (0.2 × recency) + (0.1 × specificity) + (0.1 × feedback_history)
```

Where:
- **base_rate:** Number of observations supporting the pattern / total observations in the window
- **consistency:** Number of consecutive windows where the pattern held / total consecutive windows
- **recency:** `min(1.0, max_support_weight × e^(-λ × windows_since_last_support))` where λ = 0.5
- **specificity:** How narrowly defined the pattern is (e.g., "always prioritizes urgent over important" scores higher than "sometimes prioritizes urgent tasks")
- **feedback_history:** Past operator response to patterns of this type: `(acceptances - rejections) / total_reviews`

Thresholds:
- `>= 0.7`: High confidence — surface prominently in review interfaces
- `>= 0.4 and < 0.7`: Medium confidence — surface in scheduled reviews only
- `< 0.4`: Low confidence — store for internal calibration only

### Part 4: Feedback is a first-class observation

When the operator reviews a candidate, the response is itself an observation (OBS-...) that feeds back into the learning engine:

| Action | Observation type | Effect |
|---|---|---|
| Accept | `pattern_accepted` | Confidence +0.1; may promote to inferred persona |
| Accept with modification | `pattern_modified` | Confidence +0.05; modified attributes updated |
| Reject | `pattern_rejected` | Confidence -0.2; pattern deprioritized |
| Reject with reason | `pattern_rejected_with_reason` | Confidence -0.3; pattern type weighted negatively |
| Dismiss | `pattern_dismissed` | Confidence decays 0.05 per cycle for 3 cycles; then archived |
| Snooze | `pattern_snoozed` | Confidence frozen; resurfaces at specified date |

Three consecutive rejections of the same pattern type within 30 days trigger automatic archival of all pending patterns of that type.

### Part 5: Patterns have a lifecycle

```
detected → candidate → surfaced → reviewed (accept/reject/modify/dismiss/snooze)
                                    ↓
                              active (accepted) or archived (rejected/dismissed)
                                    ↓
                              superseded (by new pattern) or promoted (to canonical)
```

- **detected:** Initial detection, below surface threshold
- **candidate:** Above surface threshold, awaiting operator review
- **surfaced:** Presented to operator via review interface
- **active:** Accepted by operator, part of inferred persona
- **archived:** Rejected, dismissed, or expired (no supporting data for 90 days)
- **superseded:** Replaced by a newer, higher-confidence pattern on the same attribute
- **promoted:** Operator explicitly promoted to canonical persona (rare — requires deliberate action)

### Part 6: Predictions are self-evaluating

Every prediction generated by the learning engine includes:
- A **prediction window** (start date, end date)
- A **prediction outcome** (null until the window closes)
- A **confidence score** (from the source pattern's confidence)

When the prediction window closes, the system automatically evaluates the outcome:
- If confirmed: source pattern confidence +0.1
- If refuted: source pattern confidence -0.2
- If neither (ambiguous): no change

This enables the system to calibrate its own understanding over time.

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Five-stage pipeline with deterministic confidence (this decision)** | Clear stages; confidence is reproducible; feedback is well-defined; consistent with ADR-009 two-layer split | Requires model for Stages 2 and 3 (pattern detection and reconciliation); deterministic confidence is less adaptive than learned confidence |
| **Pure AI end-to-end** | Maximum pattern detection capability; can adapt to novel patterns | Black box: confidence not auditable, patterns not explainable, feedback not traceable; violates Principle 7 and local-first preference |
| **Rules-only pattern detection (no AI)** | Fully deterministic; available without model; simple to implement | Cannot detect complex patterns (preference divergence, behavioral bias, energy correlation); limited to explicit rule triggers |
| **Store patterns in persona store** | Fewer stores; simpler architecture | Persona store is canonical; mixing inferred and canonical violates Principle 7; lifecycle management becomes ambiguous |
| **No learning until Phase 8** | Reduced scope; focus on deterministic executive function first | Risk of building stores optimized for recall but not inference; may need to restructure stores later |

---

## Rationale

The five-stage pipeline with deterministic confidence was chosen because:

- **Consistency with ADR-009:** This is explicitly Layer 2 of the executive reasoning engine. The deterministic confidence formula ensures that the confidence score is reproducible and auditable even though the pattern detection itself requires AI.

- **Feedback loop closure:** Making feedback a first-class observation (OBS-...) means the learning engine's own performance is auditabl. The operator can review not just "what did the system suggest" but "how did I respond to suggestions."

- **Automatic prediction evaluation:** Self-evaluating predictions enable the system to calibrate without operator effort. The operator does not need to manually confirm or refute predictions — the system evaluates them when the prediction window closes.

- **Rejection-as-signal:** Treating consistent rejection as a meaningful signal (pattern type deprioritization after 3 rejections) prevents the system from nagging. A system that keeps suggesting the same rejected pattern type erodes operator trust.

- **Lifecycle prevents stale understanding:** Patterns that are neither confirmed nor refuted are archived after 90 days. This prevents the system from operating on outdated understanding.

---

## Consequences

**Positive:**
- Clear governance boundary: all inferences are derived; promotion is operator-controlled
- Confidence is deterministic and auditable — not a model black box
- Feedback is a first-class observation, enabling the system to learn from its own performance
- Patterns have explicit lifecycle and decay; stale understanding is automatically pruned
- Self-evaluating predictions enable calibration without operator effort

**Negative:**
- Pattern detection (Stages 2 and 3) requires AI model access — unavailable during model downtime
- Confidence formula requires tuning; initial thresholds are guesses until operational data accumulates
- Three additional stores (inferred patterns, contradictions, predictions) add complexity
- Prediction self-evaluation requires careful implementation to avoid false outcomes

**Neutral:**
- The learning engine is part of Layer 6b (executive daemon), scheduled on a cadence
- It reads from existing stores (observations, persona) and writes to new stores
- It is additive — existing executive function (Layer 1, deterministic) is unaffected

---

## Risks

| Risk | Mitigation |
|---|---|
| Pattern detection is too noisy | Conservative surface thresholds; confidence floor of 0.4 for surfacing; operator can mute pattern types |
| Confidence thresholds are wrong | Configurable per-operator; defaults tunable from operational data |
| Operator ignores all candidates | Dismissed pattern types are archived after 3 cycles; system learns which pattern types to suppress |
| Feedback observations overwhelm the store | Feedback observations follow same retention/aggregation policy as other observations (ADR-008 Part 4) |
| Self-evaluating predictions mis-evaluate | Prediction outcome evaluation is deterministic; ambiguous outcomes leave confidence unchanged |
| AI model dependency blocks pattern detection | Pattern detection is scheduled, not continuous; graceful absence means patterns are simply not updated until model is available |

---

## Related artifacts

- [DOC-009 — Learning Architecture Analysis](../architecture/learning-architecture-analysis.md) — analysis this ADR formalizes
- [ADR-009 — Executive Reasoning Engine Pattern](0009-executive-reasoning-engine-pattern.md) — Layer 2 houses this learning engine
- [ADR-008 — Observation Store Architecture](0008-observation-store-architecture.md) — raw material for pattern detection
- [ADR-007 — Identity as Domain Object](0007-identity-as-domain-object.md) — canonical persona for reconciliation
- [Architecture Principle 7 — Canonical vs Derived](../architecture/principles.md) — all inferences are derived
