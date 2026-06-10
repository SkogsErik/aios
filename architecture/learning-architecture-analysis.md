# Learning Architecture: From Remembering to Understanding

**ID:** DOC-009
**Status:** Draft
**Last reviewed:** 2026-06-10
**Parent:** VIS-001

---

## Purpose

Define how AIOS moves from *remembering* (storing and recalling declared facts and observed events) to *understanding* (detecting behavioral patterns, reconciling actions with values, building a predictive model of the operator, and evolving that model through feedback). This analysis identifies the concrete mechanisms, pipeline architecture, confidence model, and feedback loops required.

---

## 1. The gap

### What "remembering" gives us

The current architecture (Phase 5) provides persistent stores for:

- **Declared facts:** "I value deep work over meetings." (Persona store, canonical)
- **Observations:** "Attended 4 meetings today, completed 0 deep work sessions." (Observation store)
- **Projects and commitments:** "PRJ-042 deadline is Friday." (Project store)

The system can answer: *"What did you say on date X?"* and *"What happened on date Y?"*

### What "understanding" requires

The system cannot answer:

- *"You said you value deep work, but your last 30 days show 80% meeting time. Should we adjust your schedule or your stated value?"*
- *"You've rejected every AI suggestion this month. Should we reduce the suggestion rate or improve quality?"*
- *"You consistently switch projects every 3 days. This reduces completion rate. Would you like to set a minimum focus period?"*
- *"You work best in the morning, but you scheduled PRJ-042 review for 15:00. Your historical completion rate at that time is 30%."*

The gap between these two sets of questions is the gap between **storage** and **inference**. The first set requires only retrieval. The second requires:

1. **Pattern detection:** Identifying recurring behavior across observations
2. **Reconciliation:** Comparing detected patterns against declared values
3. **Confidence modeling:** Assigning reliability to detected patterns
4. **Prediction:** Forecasting future behavior from past patterns
5. **Feedback integration:** Incorporating operator responses to refine the model

---

## 2. Inference pipeline

The learning architecture uses a five-stage pipeline that runs on a scheduled cadence (Layer 2 of ADR-009, Phase 7):

```
Observations ──► Stage 1: Aggregation
                     │
                     ▼
               Stage 2: Pattern Detection
                     │
                     ▼
               Stage 3: Reconciliation
                     │
                     ▼
               Stage 4: Confidence Scoring
                     │
                     ▼
               Stage 5: Candidate Generation
                     │
                     ▼
               Operator Review ──► Accepted ──► Persona Update
                     │
                     └──► Rejected ──► Confidence Decay
```

### Stage 1 — Aggregation

Raw observations are grouped into meaningful windows: daily, weekly, monthly, quarterly. Aggregation answers *"what happened in this time window?"* at different resolutions.

**Key aggregations:**
- Time allocation per project per day/week/month
- Activity type breakdown (meetings, deep work, admin, correspondence)
- Energy level distribution (high/medium/low)
- Decision outcomes (what was decided, what was the result)
- Project velocity (attention per project over time)

### Stage 2 — Pattern Detection

Patterns are detected by comparing aggregations across windows. A pattern is a statistically significant deviation from expectation.

**Pattern types:**

| Pattern | Definition | Example |
|---|---|---|
| Preference-behavior divergence | Declared value vs. observed behavior diverge beyond threshold | "Deep work" declared but meetings dominate calendar |
| Behavioral bias | Consistent deviation from optimal allocation | Consistently prioritizes urgent over important |
| Cyclical pattern | Project type repeats on a predictable cadence | Every Monday is planning, every Friday is review |
| Attention cliff | Project attention drops abruptly | 14 days active → 0 attention; not normal decay |
| Delegation pattern | Specific categories consistently deprioritized | "Infrastructure" projects always slip |
| Energy correlation | Activity X correlates with energy level | Deep work only happens on high-energy days |
| Completion signature | Conditions associated with project completion | Projects with written specs complete at 80% vs 30% |
| Rejection pattern | AI suggestion rejection correlates with X | All rejected suggestions share a common tag |

### Stage 3 — Reconciliation

Reconciliation compares detected patterns against the canonical persona. The output is a set of **tensions** — areas where the operator's behavior contradicts their declared values or preferences.

**Reconciliation algorithm:**
1. For each declared preference, compute an observed score from observations
2. If |declared - observed| > threshold, flag as a tension
3. Classify tension severity: minor, moderate, critical
4. For tensions that persist across 3+ consecutive windows, escalate to pattern status

**Example:**
```
Declared: deep_work_weight = 0.8 (80% of productive time should be deep work)
Observed (30 day): deep_work_actual = 0.25
Tension: critical (|0.8 - 0.25| = 0.55 > 0.3 threshold)
Pattern: persistent, verified across 3 weekly windows
Suggestion: "Reduce meeting load or update deep_work_weight"
```

### Stage 4 — Confidence Scoring

Every detected pattern receives a confidence score. This score determines how the pattern is surfaced (if at all) and how much weight it carries.

**Confidence factors:**

| Factor | Weight | Description |
|---|---|---|
| Base rate | 0.3 | How many observations support this pattern |
| Consistency | 0.3 | How often the pattern holds vs. breaks |
| Recency | 0.2 | Weighted by newer observations |
| Specificity | 0.1 | How specific vs. vague the pattern is |
| Feedback history | 0.1 | Past operator response to similar patterns |

**Thresholds:**
- `>= 0.7`: High confidence — surface for review; may influence derived persona
- `>= 0.4 and < 0.7`: Medium confidence — surface in weekly review only
- `< 0.4`: Low confidence — store but do not surface; used for internal model calibration

### Stage 5 — Candidate Generation

Patterns above the surface threshold are formatted as **candidates** for operator review. Each candidate contains:

```yaml
candidate_id: CND-20260610-001
pattern_type: preference_behavior_divergence
confidence: 0.72
title: "Deep work vs meeting time divergence"
description: "Your stated value is 80% deep work, but the last 30 days show 25% deep work and 60% meetings."
evidence:
  - window: "2026-06-03 to 2026-06-10"
    deep_work_pct: 30
    meeting_pct: 55
  - window: "2026-05-27 to 2026-06-03"
    deep_work_pct: 22
    meeting_pct: 62
  - window: "2026-05-20 to 2026-05-27"
    deep_work_pct: 24
    meeting_pct: 58
suggestions:
  - "Block daily deep work time before noon (highest energy period)"
  - "Decline meetings that don't require your direct input"
  - "Update stated deep_work_weight to reflect actual allocation"
requires_review: true
```

### Feedback Integration

When the operator reviews a candidate, the outcome feeds back into the learning engine:

| Action | Effect |
|---|---|
| Accept | Pattern confidence increases; may promote to canonical persona |
| Accept with modification | Pattern adjusts to operator's correction; confidence increases |
| Reject | Pattern confidence decreases; pattern is deprioritized |
| Reject with reason | Pattern type receives a negative weighting for future candidates |
| Dismiss (ignore) | Pattern confidence decays gradually over 3 cycles; then archived |
| Snooze (remind later) | Pattern resurfaces at a specified future date |

---

## 3. The model: what understanding looks like

The system moves through three levels of understanding:

### Level 1 — Descriptive ("What happened")
- Aggregates observations into summaries
- Answers: "This week, you spent 10h on PRJ-042 and 5h on PRJ-038"
- **Available now** (Phase 5 observation store)

### Level 2 — Diagnostic ("Why it matters")
- Detects patterns and compares against declared values
- Answers: "Your stated priority is PRJ-042, but PRJ-038 received 2x the attention"
- **Requires:** Pattern detection + reconciliation (Stage 2 + 3)

### Level 3 — Predictive ("What to expect")
- Forecasts behavior from historical patterns
- Answers: "Based on the last 3 projects of this type, you'll likely deprioritize this in week 2. Would you like to set a reminder to review at that point?"
- **Requires:** Pattern persistence + confidence modeling (Stage 4) + predictive model

---

## 4. Store extensions

To support understanding, three new stores or store extensions are needed:

### 4.1 Inferred Pattern Store

Where detected patterns live (separate from canonical persona). Each pattern has lifecycle, confidence, evidence, and feedback history.

```yaml
# Schema: InferredPattern
id: PAT-YYYYMMDD-NNN
status: candidate | active | archived | superseded
pattern_type: preference_divergence | behavioral_bias | cyclical | attention_cliff | ...
confidence: float  # 0.0–1.0

detected:
  first: ISO8601    # When first detected
  latest: ISO8601   # Most recent confirmation
  count: int         # Number of confirmation windows

evidence:
  - window_start: ISO8601
    window_end: ISO8601
    metrics: {...}   # Supporting data

canonical_reference: PRS-001  # Related persona attribute (if any)
suggestions: [string]          # Remediation suggestions

feedback:
  status: pending | accepted | rejected | dismissed | modified
  operator_note: string | null
  reviewed_at: ISO8601 | null
```

### 4.2 Contradiction Store

Tensions are tracked as first-class entities so they can be revisited.

```yaml
# Schema: Contradiction
id: CTR-YYYYMMDD-NNN
status: active | resolved | superseded
declared:                    # The canonical value being contradicted
  attribute: deep_work_weight
  value: 0.8
observed:                   # The observed value
  attribute: deep_work_actual
  value: 0.25
  window: 30d               # Time window of observation
magnitude: 0.55             # |declared - observed|
threshold: 0.3              # The threshold that was exceeded
pattern_ref: PAT-... | null # Related pattern
```

### 4.3 Preference Prediction Store

Forward-looking predictions derived from patterns.

```yaml
# Schema: Prediction
id: PRD-YYYYMMDD-NNN
status: active | confirmed | refuted | expired
prediction_target: "Project PRJ-042 will be deprioritized in week 2"
confidence: 0.68
based_on:
  - PAT-...  # Source pattern(s)
window_start: ISO8601
window_end: ISO8601
outcome: null | confirmed | refuted
```

---

## 5. Phasing

| Phase | Capability | Dependency |
|---|---|---|
| Phase 5 | Observation store, Persona store | ADR-007, ADR-008 |
| Phase 6 | Rules engine (deterministic) | ADR-009 Layer 1 |
| Phase 7a | Pattern detection (Stage 1 + 2) | Phase 5 + Layer 2 AI |
| Phase 7b | Preference reconciliation (Stage 3) | Phase 7a |
| Phase 7c | Confidence model + feedback (Stage 4 + 5) | Phase 7b |
| Future | Predictive model (Level 3) | Phases 7a–c + operator feedback history |

---

## 6. Key design decisions for ADR-011

1. **Inferred patterns are always derived** — never promoted to canonical without operator review
2. **Confidence scoring is deterministic** — the confidence formula is a fixed function, not model-dependent
3. **Feedback is first-class** — operator responses to patterns are themselves observations and feed the learning cycle
4. **Rejection is a signal** — patterns the operator consistently rejects reveal boundaries in the operator's self-model
5. **Patterns decay** — unconfirmed patterns lose confidence over time and are archived
6. **Predictions are self-evaluating** — every prediction includes a window and outcome; confirmed predictions increase confidence, refuted predictions decrease it

---

## 7. Related artifacts

- [ADR-009 — Executive Reasoning Engine Pattern](../adr/0009-executive-reasoning-engine-pattern.md) — Layer 2 (AI reasoning) houses this architecture
- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md) — raw material for pattern detection
- [ADR-007 — Identity as Domain Object](../adr/0007-identity-as-domain-object.md) — persona stores for declared values
- [ADR-011 — Learning Architecture](../adr/0011-learning-architecture.md) — formal decisions for this document
- [DOC-017 — Executive Cognition Analysis](executive-cognition-analysis.md) — predecessor analysis
- [Principle 7 — Canonical vs Derived](../architecture/principles.md) — governs all inference outputs
