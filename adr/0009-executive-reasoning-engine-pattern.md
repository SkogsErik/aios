# 0009 — Executive Reasoning Engine Pattern

**ID:** ADR-009
**Status:** Accepted
**Date:** 2026-06-10
**Affects:** CAP-004, CAP-009, CAP-003, THEME-004, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

DOC-017 (Executive Cognition Analysis) describes an executive reasoning engine that computes priorities, allocates attention, generates decision support, and triggers reflection cycles. The analysis presents these as related capabilities but does not distinguish between two fundamentally different classes of computation:

**Deterministic computation:** Rules-based, no model dependency, always available, fully predictable. Examples include attention decay functions, deadline proximity scoring, stall detection, and fragmentation alerts.

**AI-assisted reasoning:** Model-dependent, probabilistic, requires evaluation gate. Examples include pattern detection in observation streams, decision context assembly, preference learning, and insight extraction from reflection cycles.

Conflating these in a single architecture creates several problems:
- The entire system becomes dependent on model availability for basic functions
- Development timelines are coupled — priority computation cannot ship until pattern detection is ready
- Governance requirements are blurred — deterministic rules and AI inferences have different risk profiles
- Graceful degradation is impossible — when the model is unavailable, the entire engine fails

This ADR separates these two layers and defines the boundary between them.

---

## Decision

### Part 1: Two-layer architecture

The executive reasoning engine is split into two distinct layers:

```
┌─────────────────────────────────────────────────────┐
│  Layer 2: AI Reasoning                              │
│  Model-dependent, scheduled, requires review        │
│                                                      │
│  ● Pattern detection (observation streams)           │
│  ● Decision context assembly (past similar cases)    │
│  ● Preference learning (behavioral analysis)         │
│  ● Insight extraction (reflection cycles)            │
│  ● Anomaly detection (behavioral deviation)          │
│                                                      │
│  Always produces derived output (Principle 7)        │
│  Never modifies persona without human review          │
└──────────────────────┬──────────────────────────────┘
                       │ Consumes
                       ▼
┌─────────────────────────────────────────────────────┐
│  Layer 1: Rules Engine                               │
│  Deterministic, always-on, no model dependency       │
│                                                      │
│  ● Attention decay computation                       │
│  ● Deadline proximity scoring                        │
│  ● Stall detection (X days without attention)        │
│  ● Commitment urgency ranking                        │
│  ● Fragmentation alerts (active > 3, dormant > 15)   │
│  ● Dependency graph traversal                        │
│  ● Priority scoring (deterministic factors only)     │
│                                                      │
│  Runs on every trigger cycle (time/event/pattern)     │
│  Produces deterministic outputs with no AI dependency │
└──────────────────────┬──────────────────────────────┘
                       │ Reads from
                       ▼
┌─────────────────────────────────────────────────────┐
│  Shared stores                                       │
│  Projects, Commitments, Observations, Persona,       │
│  Goals, Risks                                        │
└─────────────────────────────────────────────────────┘
```

### Part 2: Layer 1 — Rules Engine (deterministic)

The rules engine is a deterministic state machine that operates on every trigger cycle (configurable: every 5 minutes when active, every hour when idle). It requires no model gateway access.

**Core functions:**

1. **Attention decay computation:** For each tracked item (project, commitment, decision), compute `attention_level = base_importance × e^(-λ × days_since_last_attention)`. Transition items between active/dormant/forgotten states at defined thresholds.

2. **Stall detection:** Any active project with no attention for 7+ consecutive days generates a stall alert. Configurable threshold per project type.

3. **Commitment urgency ranking:** Sort commitments by (deadline proximity × commitment_weight). Commitments within 48 hours generate urgency alerts. Overdue commitments escalate daily.

4. **Fragmentation detection:** If active items > 3 or dormant items > 15, generate fragmentation warning with recommended candidates for deprioritization.

5. **Dependency graph traversal:** When a project's dependency resolves (blocked-by item transitions to completed), generate unblocking alert.

6. **Priority scoring (deterministic component only):** Compute `deterministic_priority = deadline_urgency × commitment_weight × momentum_factor`. This produces a baseline priority that the AI layer can refine but cannot override entirely.

**Outputs:**
- Stall alerts (to attention budget display)
- Deadline warnings (to attention budget display)
- Fragmentation notices (to attention budget display)
- Unblocking notifications (to operator)
- Baseline priority ranking (to AI layer for refinement)

### Part 3: Layer 2 — AI Reasoning (model-dependent)

The AI reasoning layer is scheduled (triggered on a cadence rather than running continuously). It consumes the rules engine's outputs and adds AI-assisted analysis. All outputs are labelled as derived (Principle 7) and require operator review before influencing the persona.

**Core functions:**

1. **Pattern detection:** Scan observation streams for recurring sequences. "You usually do X before Y." "You deprioritize Z when deadline pressure is high." Produces pattern observations tagged for operator review.

2. **Decision context assembly:** For a pending decision, retrieve past similar decisions from the decision store. Summarize options chosen, outcomes, and operator satisfaction. Present as decision brief.

3. **Preference learning:** From observation and decision history, infer preferences. "You consistently chose simpler architectures over more feature-rich ones." Present as candidate preference for operator review.

4. **Insight extraction (reflection cycles):** On scheduled reflection cycles (daily/weekly/monthly/quarterly), synthesize observations into insights. See DOC-017 §5 for full reflection architecture.

5. **Anomaly detection:** Compare current behavior against historical patterns. "You normally spend 2+ hours on PRJ-042 weekly. You've spent 0 hours this week." Flag for attention.

**Governance controls:**
- All AI reasoning outputs are labelled as derived (Principle 7)
- No AI output automatically modifies the persona
- Preference suggestions require explicit operator approval
- Pattern detection accuracy is logged and reviewable
- AI reasoning layer operates at autonomy stage determined by the autonomy maturity model

### Part 4: Integration

The two layers share stores (projects, commitments, observations, persona) but have different execution models:

| Dimension | Layer 1 (Rules) | Layer 2 (AI) |
|---|---|---|
| Execution | Continuous, every trigger cycle | Scheduled, on cadence |
| Model dependency | None | Requires model gateway |
| Output status | Deterministic, always available | Derived, requires review |
| Degradation | Always functional | Graceful absence (non-deterministic features unavailable) |
| Autonomy stage | Stage 0 (no AI required) | Per autonomy maturity model |

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Two-layer architecture (this decision)** | Clear separation of concerns; graceful degradation; different governance per layer; deterministic layer can ship independently | Two components to build and maintain; integration surface between layers |
| **Single monolithic engine** | Simpler architecture; one component | Entire system depends on model availability; development timeline coupled; governance boundary unclear; no graceful degradation |
| **AI-only (no deterministic rules)** | Maximum pattern capability | No output when model unavailable; over-engineered for basic functions like stall detection |
| **Rules-only (no AI)** | Fully deterministic; simple; reliable; no model dependency | Cannot detect patterns, learn preferences, or extract insights — misses the core value of executive cognition |

---

## Rationale

The two-layer approach was chosen because:

- **Graceful degradation is essential.** The system should continue to provide value (stall alerts, deadline warnings, fragmentation notices) even when no model is available. The rules engine runs offline, locally, with zero dependencies.

- **Independent shipping timelines.** The rules engine can be built, tested, and delivering value before any AI reasoning capability exists. This is consistent with the "simply founded" principle (Principle 6) and the autonomy maturity model's staged approach.

- **Governance boundary is clear.** Rules engine outputs are factual (project X has been stalled for 14 days). AI reasoning outputs are interpretive (you seem to deprioritize projects that require external coordination). These have different governance requirements.

- **Resilience.** If the model gateway fails or the local model is unavailable, the executive function degrades gracefully rather than failing entirely.

- **Consistent with existing architecture.** The deterministic layer parallels the existing workflow executor (reliable, auditable, CLI-invocable). The AI layer parallels the existing model gateway (governed, auditable, model-agnostic).

---

## Consequences

**Positive:**
- Executive function delivers value from day one (rules engine) without waiting for AI capabilities.
- The system degrades gracefully when models are unavailable.
- Development can proceed independently on two layers with different timelines.
- Governance is scoped appropriately per layer.

**Negative:**
- Two components to build, test, and maintain instead of one.
- Integration between layers must be explicitly designed (how does the AI layer consume and refine rules engine outputs?).
- The transition from Layer 1 only to Layer 1 + Layer 2 operation requires a stage transition in the autonomy maturity model.

**Neutral:**
- The rules engine can be a Python module in the executive runtime (see ADR-010).
- The AI reasoning layer is a consumer of the model gateway, consistent with ADR-002.
- Both layers read from the same stores; there is no data duplication.

---

## Risks

| Risk | Mitigation |
|---|---|
| Rules engine becomes too simple to be useful | Start simple; add deterministic rules as patterns emerge from operational experience |
| AI layer produces inaccurate patterns that are trusted | All AI outputs are derived; pattern accuracy is logged and reviewed; promotion requires operator approval |
| Two layers produce conflicting recommendations | Rules engine outputs are factual (deadline: 48h); AI outputs are interpretive (you might want to prioritize X). Explicitly scoped to prevent conflict |
| Development effort split between two layers delays both | Build Layer 1 first with full value; Layer 2 is additive with no hard dependency |

---

## Related artifacts

- [DOC-017 — Executive Cognition Analysis](../architecture/executive-cognition-analysis.md) — analysis requiring this pattern
- [DOC-018 — Pivot Readiness Assessment](../architecture/pivot-readiness-assessment.md) — peer review that identified the missing deterministic/AI boundary
- [ADR-002 — Model Gateway Pattern](0002-model-gateway-pattern.md) — AI reasoning layer is a consumer of the gateway
- [Architecture Principle 6 — Simple Foundations](../architecture/principles.md) — rules engine embodies this principle
- [Architecture Principle 7 — Canonical vs Derived](../architecture/principles.md) — applies to all AI reasoning outputs
