# Executive Cognition Analysis

**ID:** DOC-017
**Status:** Active
**Last reviewed:** 2026-06-10
**Parent:** DOC-016
**Related:** DOC-003, DOC-004, DOC-005, DOC-010, ADR-004

---

## Purpose

DOC-016 (Identity-Centric Pivot Analysis) proposed evolving AIOS from a capability-centric platform toward an identity-centric one, introducing Persona, Observation, Goal, Decision, Preference, Belief, Habit, Relationship, and Reflection as first-class concepts.

This document challenges that analysis. It argues that DOC-016, while a necessary step, remains fundamentally a *memory architecture* — a system optimized for capturing, storing, and retrieving personal data rather than one optimized for understanding, prioritizing, and acting.

The goal of this document is to identify the remaining 20% of conceptual architecture required to move from:

```
Personal Memory System
```

to:

```
Digital Executive Assistant
Personal Cognitive Extension
High-Fidelity Digital Persona
```

The focus is conceptual architecture, not implementation.

---

## 1. Critique of the Identity-Centric Analysis

### The unconscious inheritance

DOC-016 was written by someone who still thinks in terms of repositories, documents, workflows, and traceability — because those are the tools the existing architecture provides. The analysis was an honest attempt to pivot, but the underlying mental model remained:

**"Add more things to store."**

The identity-centric analysis introduces new *storage schemas* (observations, goals, decisions, preferences) and new *traceability chains* (Persona -> Goal -> Decision -> Observation -> Reflection), but the implicit operating model is unchanged:

```
Capture -> Store -> Retrieve -> Display
```

This is a personal database about the operator rather than a cognitive extension *of* the operator.

### Specific weaknesses

| Weakness | Evidence in DOC-016 | Why it matters |
|---|---|---|
| **Storage-first thinking** | Every new concept comes with a schema, a store, an identifier prefix, and a CLI command. The analysis asks "what should we store?" more than "what should we do?" | The system accumulates data but doesn't act on it. |
| **No attention model** | Attention appears nowhere in the ontology. The analysis has no concept of focus, distraction, decay, or resurfacing. | The system doesn't distinguish between what matters now vs what mattered once. |
| **No prioritization mechanism** | Goals exist but there's no model for ranking competing claims on the operator's time. | The system knows what the operator wants but can't help them choose *what to do next*. |
| **Projects absent** | Goals exist but projects — the actual unit of human productivity — are missing. | The system operates at the wrong level of abstraction for daily work. |
| **Reflection as batch process** | Reflection is a periodic analysis *after the fact*. It doesn't influence real-time attention or decision-making. | Learning happens in retrospect but doesn't shape current behavior. |
| **No commitment tracking** | Goals and decisions don't capture the weight of promises made to others. | The system misses one of the strongest drivers of human behavior. |
| **No resource model** | No concept of energy, cognitive load, or attention capacity. | The system plans as if the operator has infinite resources. |
| **Reactive by default** | Every function is triggered by CLI, workflow, or scheduled cycle. Nothing responds to events in real time. | Proactive behavior is limited to "at scheduled time X, do Y." |
| **Hidden assumptions from DOC-004** | The 8-layer architecture is carried forward with "extend Layer 4, expand Layer 2" but the fundamental question of what the system *does* at runtime is not re-examined. | The architecture remains organized around platform layers, not cognitive functions. |

### The risk

The identity-centric analysis risks building a **"sophisticated personal database"** — a system that knows everything about the operator but does nothing with that knowledge. It answers "what do I know about the operator?" but not "what should the operator do right now?"

A memory system remembers.
An executive assistant *understands*.

Understanding requires:
- Synthesis (not just accumulation)
- Prioritization (not just categorization)
- Attention management (not just storage)
- Executive reasoning (not just retrieval)
- Continuous sense-making (not just periodic reflection)

---

## 2. Missing Domain Concepts

### Evaluation

#### Project (PRJ) — YES, first-class

**Role in executive cognition:** The primary unit of human productivity. Projects are how people organize work, allocate attention, track progress, and experience completion. Goals are aspirational; projects are operational. Without projects, the reasoning engine has no concrete object to reason about.

Projects have:
- Temporal boundaries (start, target, completion)
- Resource commitments (time, attention, energy)
- Health status (on track, at risk, stalled, blocked)
- Decision density (active projects generate the most decisions)
- Attention requirement (active projects consume attention; projects are the natural unit of attention allocation)

**Where it fits:**
```
Persona
  └── Values
        └── Goals (why)
              └── Focus Areas (quarterly theme)
                    └── Projects (what)
                          ├── Decisions
                          ├── Commitments
                          └── Attention
```

---

#### Commitment (CMT) — YES, first-class

**Role in executive cognition:** A promise made to self or others. Commitments carry social weight that goals do not. Breaking a commitment damages trust; abandoning a goal is neutral. Commitments generate urgency, anxiety, and motivation. They are one of the strongest drivers of human attention and behavior.

A commitment has:
- A promisee (self or named other)
- A deliverable (what was promised)
- A deadline or trigger condition
- A risk level (how likely is this to be broken?)
- Consequences (what happens if broken)

**Executive function:** "What have I promised that I'm at risk of breaking?"

Commitments are not a subtype of goals. A goal can exist without a commitment. A commitment always implies a goal but adds the accountability dimension.

---

#### Priority (PRI) — YES, but as a computed relationship, not a stored entity

**Role in executive cognition:** Priority is the executive function of ranking competing claims on attention. It is inherently contextual — what matters right now depends on deadlines, dependencies, energy, commitment weight, and recent attention. Priority cannot be meaningfully stored as a static property because it changes with context.

**Architecture:** Priority is the **output of the executive reasoning engine**, not a stored value. Projects and commitments have base importance (stored), but current priority is computed dynamically.

---

#### Attention — YES, as a first-class architectural concern (not an entity)

**Role in executive cognition:** Attention is the finite resource that determines what the system and operator focus on. It has states (active, dormant, forgotten, resurfaced), decay functions, triggers, and capacity limits. It is the most constrained resource in the system.

**Architecture:** Attention is not an entity with an ID. It is a **subsystem** — the Attention Manager — that tracks, models, and allocates attention across all other entities. See Section 4 for the full design.

---

#### Focus Area (FCA) — YES, first-class

**Role in executive cognition:** A sustained attention commitment over weeks or months. Higher-level than projects, more concrete than goals. "Q3 focus: system architecture." Focus areas align projects with strategic intent and provide the context for priority computation.

**Relationship:**
- Goals provide direction ("become a better architect")
- Focus areas provide theme ("this quarter, focus on distributed systems")
- Projects provide execution ("design event sourcing for project X")

---

#### Responsibility (RSP) — YES, first-class

**Role in executive cognition:** Ongoing accountability without a fixed end date. "I am responsible for code quality." Responsibilities generate recurring commitments and shape attention patterns. They persist beyond individual projects and goals.

Responsibilities explain why certain commitments exist. "I promised to review this PR" because "I am responsible for code quality."

---

#### Initiative (INT) — Subtype of Project

**Role in executive cognition:** A project that is explicitly change-oriented or strategic. Distinction from a routine project matters because initiatives carry different risk profiles and attention patterns. An initiative changes the status quo; a project delivers within it.

**Architecture:** Modeled as `Project` with `type: initiative | project | maintenance`.

---

#### Opportunity (OPP) — YES, first-class

**Role in executive cognition:** A potential future value that has not been committed to. Opportunities compete for attention with active projects. They may become projects if pursued. They may be forgotten if not. Tracking opportunities separately from projects allows the system to resurface them when context changes.

**Executive function:** "What promising things am I not pursuing?"

---

#### Risk — YES, first-class

**Role in executive cognition:** A potential negative outcome with probability and impact. Risks influence priorities (high-risk items demand attention), decisions (options that reduce risk are preferred), and project health. Without a risk model, the system cannot help the operator avoid problems — only react to them.

**Properties:**
- Probability (low, medium, high)
- Impact (low, medium, high)
- Status (active, mitigated, realized, expired)
- Owner (who is responsible for monitoring)
- Mitigation plan

**Relationship to Decision:** Risks are inputs to decisions. A decision without risk awareness is incomplete.

---

#### Constraint (CON) — YES, first-class

**Role in executive cognition:** A boundary condition that limits options. Deadlines, budgets, technical limitations, personal limits, policies. Constraints shape the decision space. Without modeling constraints, the system proposes solutions that violate the operator's real-world boundaries.

**Properties:**
- Type (time, resource, technical, personal, social)
- Scope (which projects/goals it affects)
- Severity (hard, soft, negotiable)

---

#### Energy — NO, not first-class

Energy is a **measured state** on the Persona, not a separate entity. It varies by time of day, activity type, and recent history. It influences attention allocation (high-energy tasks in high-energy periods) but is not a domain object with its own lifecycle.

**Architecture:** Time-series dimension on Persona. Tracked as observation metadata ("energy level: high" tagged on observations). Used by the executive reasoning engine for scheduling suggestions.

---

#### Context — NO, not first-class

Context is a **computed view**, not a stored entity. It is the intersection of:
- Active projects
- Current focus area
- Recent decisions
- Immediate commitments
- Current energy and attention state

Context is the output of the attention system — the answer to "what is relevant right now?"

---

### Summary of ontology additions

| Level | Add? | Prefix | Rationale |
|---|---|---|---|
| Project | YES | PRJ | Primary unit of human productivity; attention consumer |
| Commitment | YES | CMT | Promises drive behavior differently from goals |
| Focus Area | YES | FCA | Quarterly/seasonal theme aligning projects with goals |
| Responsibility | YES | RSP | Ongoing accountabilities that persist beyond projects |
| Opportunity | YES | OPP | Potential value not yet committed to |
| Risk | YES | RSK | Potential negative outcomes shaping priorities |
| Constraint | YES | CON | Boundary conditions limiting options |
| Priority | Computed | — | Dynamic ranking, not stored property |
| Attention | Subsystem | — | Resource model, not entity |
| Energy | State | — | Persona dimension, not entity |
| Context | Computed | — | Intersection of active state, not entity |
| Initiative | Subtype | — | Project type, not separate entity |

---

## 3. Executive Reasoning Model

### Purpose

To answer:

- What deserves attention?
- What can be ignored?
- What should be delegated?
- What should be done now?
- What has changed?
- What is at risk?
- What opportunities are emerging?

This is not a query against stored data. It is a continuous reasoning process that produces *judgments*, not *results*.

### Inputs

```
Project Portfolio
├── Active projects (with health, momentum, deadline)
├── At-risk projects (blocked, stalled, overdue)
├── Paused projects (waiting, deprioritized)
└── Completed projects (recent, for pattern analysis)

Goal Status
├── Progress trajectories (ahead, on-track, behind, stalled)
├── Recent goal decisions (added, removed, reprioritized)
└── Goal dependencies (which goals depend on which)

Commitment Register
├── Upcoming deadlines
├── Overdue promises
├── Commitments without recent attention
└── Recurring commitments (standups, reviews, etc.)

Attention State
├── Current active items
├── Dormant items with decay metrics
├── Recently resurfaced items
└── Fragmentation metric (how many things are competing)

Observation Stream
├── Recent actions and decisions
├── Notes and reflections
└── External signals (calendar, messages, emails)

Risk Inventory
├── Active risks with status
├── Recently realized risks
└── Emerging risks (detected by pattern analysis)

Energy Context
├── Current time of day
├── Recent activity intensity
├── Calendar pressure (meeting density)
└── Historical energy patterns (when does operator work best)
```

### Processing

The executive reasoning engine operates as a continuous loop with four phases:

#### Phase 1: Signal Detection

Scan all inputs for signals that demand attention:

```
Urgency Signals:
  ● Deadline within 48 hours
  ● Commitment overdue
  ● Risk probability increasing
  ● Blocker resolved (dependency unblocked)
  ● New high-priority input

Momentum Signals:
  ● Active project with recent progress (protect momentum)
  ● Active project without progress for 5+ days (stall warning)
  ● Completed milestone (transition attention)

Pattern Signals:
  ● Repeated behavior (habit detected)
  ● Behavior change (departure from past pattern)
  ● Tension (conflicting values in decisions)

Opportunity Signals:
  ● Past interest resurfacing
  ● New information affecting a dormant project
  ● Constraint removed (something previously blocked is now possible)
```

Output: A ranked list of signals competing for attention.

#### Phase 2: Priority Computation

For each signal and each active item, compute:

```
priority_score = urgency_weight × urgency × importance × commitment_weight × momentum_bonus × energy_match
```

Where:

- **urgency_weight**: Time sensitivity (deadline proximity, opportunity window)
- **urgency**: Base urgency of the item type (commitments > projects > goals)
- **importance**: Impact on goals, values, and responsibilities
- **commitment_weight**: Multiplier for promised items (promises to others > promises to self)
- **momentum_bonus**: Positive for items with recent progress (protect momentum), negative for stalled items
- **energy_match**: Fit between task type and current energy level (creative work in high energy, admin in low energy)

Output: A ranked priority list with the score components visible for transparency.

#### Phase 3: Decision Context Assembly

For the top 1-3 priority items, assemble decision support context:

```
For each top-priority item:
  1. What decision is needed? (explicitly state the question)
  2. What past decisions are similar? (from decision store)
  3. What preferences apply? (from persona)
  4. What constraints are relevant? (deadlines, budgets, boundaries)
  5. What are the likely outcomes? (based on past patterns)
  6. What is the operator's likely choice? (confidence scored)
```

Output: Decision briefs that reduce the cognitive load of deciding.

#### Phase 4: Action Recommendation

From the priority list, generate actionable recommendations:

```
Immediate Action:
  "Do X now — it takes 5 minutes and unblocks Y."

Today's Focus:
  "Protect 9-11am for Z. You're in your high-energy window
   and the deadline is tomorrow."

Delegation Candidate:
  "A can be automated based on your past patterns.
   B can wait until next week."

Deprioritization:
  "C has been stalled for 3 weeks with no external change.
   Consider pausing or abandoning."

Abandonment:
  "D hasn't received attention in 60 days. Your past behavior
   suggests you're not going to return to this. Should I
   mark it as abandoned?"
```

### Outputs

```
1. ATTENTION BUDGET: Suggested focus allocation
   ┌─────────────────────────────────────────────┐
   │ Morning (high energy): PRJ-042 decision      │
   │ Afternoon (meetings): PRJ-038 status sync    │
   │ Evening (low energy): PRJ-045 review prep    │
   └─────────────────────────────────────────────┘

2. PRIORITY RANKING: What matters most right now
   ┌─────────────────────────────────────────────┐
   │ 1. PRJ-042 — Deadline tomorrow, needs dec.  │
   │ 2. CMT-015 — Promise to team, prep meeting  │
   │ 3. PRJ-038 — At risk, stalled 14 days       │
   └─────────────────────────────────────────────┘

3. DECISION BRIEF: Context for top priority
   ┌─────────────────────────────────────────────┐
   │ Decision: Architecture choice for PRJ-042    │
   │ Past pattern: You chose X for similar cases  │
   │ Preference: Simpler > flexible under deadline│
   │ Constraint: Must integrate with existing Y   │
   │ Likely choice: Option A (72% confidence)     │
   └─────────────────────────────────────────────┘

4. ATTENTION ALERT: What's being missed
   ┌─────────────────────────────────────────────┐
   │ ⚠ PRJ-038: 14 days without attention        │
   │ ⚠ CMT-015: Deadline approaching (3 days)    │
   │ ℹ PRJ-050: Blocker resolved, ready to resume│
   └─────────────────────────────────────────────┘
```

### Interaction with existing components

| Component | Role in executive reasoning |
|---|---|
| Persona | Provides values, preferences, and patterns that weight priority computations |
| Goals | Provide the outcome-based definition of importance |
| Observations | Provide the raw pattern data for signal detection |
| Decisions | Are the primary output of the reasoning engine — each recommendation implies a decision |
| Knowledge Store | Provides context for decision briefs (past similar situations documented as knowledge) |
| Model Gateway | Powers the AI-assisted pattern detection and decision context assembly |
| Workflow Runtime | Executes the actions that result from decisions |

---

## 4. Attention Architecture

### Core insight

Humans are not defined only by what they remember. They are defined by what they pay attention to. Attention is the bottleneck resource. The system that manages attention better manages the operator's cognitive life better.

### Attention states

```
                         ┌──────────────────┐
                         │                  │
     new input ─────────►│    ACTIVE        │◄──── Currently in focus
                         │  (1-3 items)     │      (projects, decisions,
                         │                  │       commitments)
                         └────────┬─────────┘
                                  │
                     decay over time (no attention)
                                  │
                                  ▼
                         ┌──────────────────┐
                         │                  │
                         │    DORMANT       │◄──── Intend to return to
                         │  (waiting)       │      (paused projects,
                         │                  │       deferred decisions)
                         └────────┬─────────┘
                                  │
                     extended inactivity (30+ days)
                                  │
                                  ▼
                         ┌──────────────────┐
                         │                  │
                         │   FORGOTTEN      │◄──── No longer in awareness
                         │  (neglected)     │      (abandoned projects,
                         │                  │       expired opportunities)
                         └────────┬─────────┘
                                  │
                     trigger condition met
                                  │
                                  ▼
                         ┌──────────────────┐
                         │                  │
                         │  RESURFACED      │◄──── Brought back by system
                         │  (proposed)      │      (suggested for review)
                         │                  │
                         └──────────────────┘
```

### Attention capacity model

```
ACTIVE:   1-3 items        (human cognitive limit — Miller's Law + 1)
DORMANT:  5-15 items       (working set — can track without overflow)
FORGOTTEN: unlimited       (system tracks; operator doesn't consciously hold)
```

**Capacity rules:**

```
if active > 3:
    → WARNING: attention fragmentation
    → Recommendation: defer or abandon lowest-priority active item

if dormant > 15:
    → WARNING: working set overflow
    → Recommendation: batch review dormant items for abandonment

if active == 0:
    → SUGGESTION: what to focus on next
    → Based on priority ranking + energy context
```

### Attention decay model

Each item (project, commitment, decision) has an attention decay function:

```
attention_level(t) = base_importance × e^(-λ × days_since_last_attention)
```

Where λ (decay rate) depends on item characteristics:

| Characteristic | Decay rate (λ) | Effect |
|---|---|---|
| High commitment weight | 0.05 | Slow decay — promises resist forgetting |
| Recurring | 0.02 | Very slow — recurring items have periodic resets |
| Active project | 0.08 | Moderate — projects decay without attention |
| Paused project | 0.12 | Faster — paused items fade |
| Decision pending | 0.15 | Fast — decisions need timely resolution |
| Opportunity | 0.20 | Fast — opportunities are time-sensitive |

When `attention_level` drops below a threshold, the item transitions:
- Below 0.5 (active): move to dormant
- Below 0.2 (dormant): move to forgotten
- Below 0.05: candidate for abandonment recommendation

### Attention triggers

What moves an item from dormant/forgotten back to resurfaced:

**Time-based triggers:**
```
- Scheduled review check (daily for active, weekly for dormant, monthly for forgotten)
- Deadline within threshold (7 days for commitments, 3 days for active projects)
- Periodic commitment (weekly standup, monthly report)
```

**Event-based triggers:**
```
- Dependency resolved → resurface blocked item
- New observation → resurface related item
- External signal → resurface relevant to incoming context
- Calendar event → resurface preparation items
```

**Pattern-based triggers:**
```
- Past pattern match → "You usually do X before Y. Y is tomorrow."
- Contrast detection → "You normally focus on this, but haven't in Z days."
- Opportunity detection → "Past interest X has new relevant information."
```

### Attention graph

Items are not isolated. They exist in an attention graph where focusing on one thing affects others:

```
PRJ-042 (active)
  ├── blocks: PRJ-043 (dormant — waiting on PRJ-042 decision)
  ├── blocked by: PRJ-040 (forgotten — needs review)
  └── related: CMT-015 (active — commitment to deliver PRJ-042)
```

The attention manager traverses this graph to:
- Suggest unblocking actions (resurface PRJ-040 if it blocks PRJ-042)
- Warn about cascading delays (PRJ-042 slip affects PRJ-043)
- Surface related commitments (CMT-015 adds weight to PRJ-042)

### Attention manager

A new architectural component (module in Layer 6):

```
AttentionManager
├── State: active, dormant, forgotten, resurfaced sets
├── Decay: per-item decay computation
├── Triggers: time, event, and pattern trigger evaluation
├── Graph: attention dependency graph
└── Output: attention budget, fragmentation alerts, resurfacing suggestions
```

**Responsibilities:**
1. Track attention state for all projects, commitments, decisions, and opportunities
2. Compute decay for all tracked items
3. Evaluate trigger conditions continuously
4. Produce attention budget recommendations (suggested focus allocation)
5. Alert on fragmentation (too many active items)
6. Alert on neglect (items decaying without attention)
7. Surface resurfacing candidates
8. Log attention transitions as observations (for pattern analysis)

---

## 5. Deep Reflection Architecture

DOC-016 introduced reflection but treated it as a periodic batch process that produces summaries. This section redesigns reflection as a **multi-cycle learning system** that generates decisions, updates the Persona, and shapes future attention allocation.

### Design principles

1. **Reflection generates decisions, not just observations.** Each cycle produces explicit choices: what to focus on, what to abandon, what to change.
2. **Each cycle feeds the next.** Daily decisions inform weekly patterns. Weekly patterns inform monthly themes. Monthly themes inform quarterly strategy.
3. **Reflection updates the Persona.** The output of reflection is not just a document — it's an updated model of who the operator is and how they operate.
4. **Reflection is governed.** Like all AIOS processes, reflection operates within bounds and produces auditable records.
5. **Reflection has diminishing granularity.** Daily is detailed. Quarterly is strategic. The system spends cognitive effort proportional to the cycle length.

### Daily reflection

**Trigger:** End of day (operator-configured time)

**Inputs:**
- Today's observation stream (decisions, actions, notes)
- Active project status changes
- Attention log (what was focused on, for how long)
- Calendar events (meetings attended, appointments)
- Completion rate (planned vs actual)

**Processing:**
```
1. Reconstruct: What happened today?
   - Sequence of events from observations
   - Decisions made and their context
   - Items completed vs deferred

2. Compare: Planned vs actual
   - What did I intend to do today?
   - What did I actually do?
   - What explains the gap? (interruption, energy, priority shift)

3. Evaluate: Decision quality
   - Were today's decisions consistent with values?
   - Were any decisions made under time pressure or low energy?
   - Which decisions should be revisited?

4. Project: Tomorrow
   - What carries forward from today?
   - What new inputs arrived?
   - What is the recommended focus?
```

**Outputs:**
```
Output                → Consumption
────────────────────────────────────────────────────
Tomorrow's attention  → Attention manager (preliminary budget)
budget (recommended)    priority ranking)

Items to carry        → Attention manager (maintain in active/dormant)
forward

Decisions flagged     → Decision store (mark for review)
for review

Observations tagged   → Observation store (add pattern-relevant tags)
for patterns

Persona: minor        → Persona (preference adjustments if behavior
preference updates      contradicts stated preferences)

Goal: daily progress  → Goal (progress notes, trajectory check)
note
```

**Decisions generated:**
- "What should I focus on tomorrow?"
- "Which decision from today should I revisit?"

---

### Weekly reflection

**Trigger:** End of week (Sunday)

**Inputs:**
- 7 daily reflection outputs
- Project status changes (milestones, health changes)
- New commitments made
- Risks identified or realized
- Attention fragmentation metrics (active count, context switches)
- Observation volume and type distribution

**Processing:**
```
1. Pattern detection:
   - What kept recurring across the week?
   - What was deferred repeatedly?
   - What was the dominant theme?

2. Momentum assessment:
   - Which projects gained momentum?
   - Which projects stalled?
   - What caused the stalls?

3. Energy analysis:
   - When was attention most focused?
   - When was attention fragmented?
   - What was the energy pattern? (peak times, low times)

4. Commitment review:
   - Were commitments met this week?
   - Which commitments are at risk for next week?
   - What new commitments were made?

5. Tension identification:
   - Did any decisions contradict stated values?
   - Did any repeated pattern suggest a tension?
```

**Outputs:**
```
Output                  → Consumption
──────────────────────────────────────────────────────
Next week's focus      → Attention manager (primary allocation)
areas (1-3)

Project priority       → Project portfolio (health updates,
adjustments              priority reordering)

Next week's decision   → Executive reasoning engine (queue
queue                    for decision support generation)

Risk register updates  → Risk inventory (new risks, status changes)

Persona: pattern       → Persona (habit detection, preference
recognition              refinement)

Goal: weekly progress  → Goal (trajectory updates, confidence
and trajectory          adjustments)

Weekly theme           → Observation store (tag for monthly pattern
                        synthesis)
```

**Decisions generated:**
- "Which project needs most attention next week?"
- "What commitment is at risk and what should I do about it?"
- "What pattern from this week should I be aware of?"
- "What should I stop doing?"

---

### Monthly reflection

**Trigger:** End of month

**Inputs:**
- 4 weekly reflection outputs
- Goal progress data (milestones, metrics)
- Project milestone completion (what was delivered)
- Commitment completion rate (promises kept vs broken)
- Decision outcome data (decisions made → actual outcomes)
- Observation statistics (volume by category, type, project)
- Attention distribution (time spent per project, per type)

**Processing:**
```
1. Strategic alignment:
   - Are current projects serving current goals?
   - Is attention allocation matching strategic priorities?
   - Are any goals being neglected?

2. Resource allocation:
   - How was time actually spent vs intended?
   - What consumed disproportionate attention?
   - What was under-attended?

3. Pattern synthesis:
   - What patterns emerged over the month?
   - Which patterns are new? Which are persistent?
   - What does the operator do consistently? What varies?

4. Abandonment analysis:
   - Which active items should be considered for pausing?
   - Which dormant items should be considered for abandonment?
   - What is the cost of continuing vs stopping?

5. Opportunity scan:
   - What past interests have new relevance?
   - What new opportunities appeared?
   - What constraints have changed?
```

**Outputs:**
```
Output                  → Consumption
──────────────────────────────────────────────────────
Next month's theme     → Focus area (primary focus declaration)

Project portfolio      → Project store (status changes,
rebalancing              pause/abandon/addition decisions)

Goal confidence        → Goal store (trajectory revisions,
updates                  scope adjustments)

Persona: belief        → Persona (value evolution, belief changes,
updates                  preference evidence)

Abandonment            → Project store (status: abandoned)
recommendations          + Decision store (abandonment rationale)

New project            → Project store (status: draft, from
suggestions              opportunity conversion)

Decision pattern       → Persona (decision model refinement)
refinements
```

**Decisions generated:**
- "Should I continue, pause, or abandon Project X?"
- "Are my current goals still aligned with my values?"
- "What should I say no to next month?"
- "What have I learned about how I work?"
- "What opportunity should I pursue?"

---

### Quarterly reflection

**Trigger:** End of quarter

**Inputs:**
- 3 monthly reflection outputs
- Quarter-level goal completion (which goals advanced, which didn't)
- Project outcomes (actual results vs intended outcomes)
- Decision outcome analysis (decisions tracked → actual results compared)
- Relationship/interaction patterns
- Value evolution signals (changes in stated or revealed preferences)
- Reflection records from all prior cycles

**Processing:**
```
1. Outcome analysis:
   - What worked? What didn't? Why?
   - What was delivered vs intended?
   - What was the gap and what caused it?

2. Decision audit:
   - Review significant decisions from the quarter
   - Compare expected outcomes vs actual outcomes
   - Identify where the decision model was accurate vs wrong

3. Value check:
   - Are actions aligned with stated values?
   - Have values changed? (revealed preference analysis)
   - Are goals still consistent with current values?

4. Learning extraction:
   - What important things were learned?
   - What should be carried forward?
   - What should be done differently?

5. Strategic direction:
   - Are we heading in the right direction?
   - What has changed in the external context?
   - Should goals be revised, added, or retired?

6. Persona evolution:
   - How has the operator changed this quarter?
   - What beliefs have been reinforced? Which have changed?
   - What new patterns emerged?
```

**Outputs:**
```
Output                  → Consumption
──────────────────────────────────────────────────────
Next quarter           → Focus area store (primary strategic
strategy                 direction)

Goal hierarchy         → Goal store (new goals, retired goals,
revision                 reprioritized goals)

Persona evolution      → Persona (value refinements, belief updates,
record                   preference changes)

Decision model         → Persona (refined understanding of
updates                  how operator decides)

Major project          → Project store (additions, removals,
portfolio changes        priority shifts)

Learning summary       → Knowledge store (synthesized as
                         knowledge asset for future reference)

Reflection record      → Reflection store (RFL-xxx, saved with
                         full audit trail)

Quarterly theme        → Observation store (tagged for
                        annual pattern synthesis)
```

**Decisions generated:**
- "What should be my primary focus for the next quarter?"
- "What goals should I abandon or revise?"
- "How has my thinking changed this quarter?"
- "What should I do differently going forward?"
- "What have I become better at? What have I lost?"

### Reflection engine architecture

```
Observation Stream (continuous)
        │
        ▼
┌──────────────────────────────────────────────────────┐
│                  REFLECTION ENGINE                   │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │  DAILY   │  │  WEEKLY  │  │ MONTHLY  │  │ QTR  │ │
│  │ cycle    │──►│ cycle   │──►│ cycle    │──►│cycle │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────┘ │
│       │              │             │           │      │
│       ▼              ▼             ▼           ▼      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │Decision: │  │Decision: │  │Decision: │  │Strat │ │
│  │tomorrow's│  │week's    │  │continue/ │  │reset │ │
│  │focus     │  │priorities│  │abandon   │  │      │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────┘ │
│                                                      │
│  Outputs flow to:                                    │
│  ├── Attention Manager (focus allocation)            │
│  ├── Persona (preferences, beliefs, values)          │
│  ├── Project Store (status, priority, health)        │
│  ├── Goal Store (progress, trajectory)               │
│  ├── Decision Store (decisions made)                 │
│  ├── Risk Inventory (new/mitigated risks)            │
│  └── Knowledge Store (learning artifacts)            │
└──────────────────────────────────────────────────────┘
```

Each cycle is a workflow definition (WF-NNN) executed by the workflow runtime. The reflection engine is an orchestrator that:
1. Triggers the appropriate cycle on schedule
2. Assembles inputs from relevant stores
3. Invokes the reflection workflow (which uses the model gateway for AI-assisted pattern analysis)
4. Writes outputs back to stores
5. Initiates decisions generated by the reflection

---

## 6. Project-Centric Operating Model

### The claim

Most real-world human activity is organized around **projects**, not goals. Goals provide direction and motivation. Projects provide structure, deadlines, resource allocation, completion criteria, and the satisfaction of *getting something done*. The question "what are you working on?" is always answered with a project, never with a goal.

### Why projects are the right unit

| Dimension | Goal | Project |
|---|---|---|
| Temporality | Continuous, ongoing | Bounded, completable |
 | Success criteria | Abstract ("be healthier") | Concrete ("run 5k in under 30 min") |
| Decision density | Low (strategic, infrequent) | High (operational, daily) |
| Attention allocation | Diffuse | Focused |
| Completion | Rarely fully achieved | Clearly completable |
| Abandonment cost | Low (can always revisit) | Higher (sunk cost, commitments) |
| Social visibility | Low (personal aspiration) | High (what you tell people you're doing) |

### Where projects fit in the ontology

```
Persona (PRS)
  └── Values (deepest layer, slowest to change)
        └── Goals (GL) — why, continuous, aspirational
              └── Focus Areas (FCA) — quarterly/seasonal theme
                    └── Projects (PRJ) — what, bounded, operational
                          ├── Tasks (execution units within projects)
                          ├── Decisions (DEC) — choices made during project execution
                          ├── Commitments (CMT) — promises related to project delivery
                          ├── Risks (RSK) — project-specific uncertainties
                          ├── Constraints (CON) — project boundaries
                          └── Attention allocation (from Attention Manager)
```

### Project model

```yaml
id: PRJ-001
title: "Implement executive reasoning engine"
type: project                    # project | initiative | maintenance
status: active                   # draft | active | paused | completed | cancelled | abandoned

hierarchy:
  goal: GL-003                   # "Build identity-centric AIOS"
  focus_area: FCA-001            # "Q3: Executive function foundation"
  parent_project: null           # for sub-projects
  sub_projects: [PRJ-002]        # decomposition

timeline:
  started: 2026-06-10
  target_completion: 2026-09-01
  actual_completion: null
  milestones:
    - id: MS-001
      name: "Design complete"
      date: 2026-07-01
      status: completed
    - id: MS-002
      name: "Core reasoning loop operational"
      date: 2026-08-01
      status: in_progress

commitments:
  - CMT-001                     # "Deliver initial version by Sept"
  - CMT-002                     # "Review with mentor by Aug"

dependencies:
  blocks: [PRJ-004]             # downstream projects waiting on this
  blocked_by: [PRJ-003]         # upstream projects blocking this

decisions: [DEC-010, DEC-011, DEC-012]
risks: [RSK-005, RSK-006]
constraints: [CON-003]

attention:
  status: active                # active | dormant | forgotten
  last_active: 2026-06-10
  days_since_attention: 0
  total_hours_allocated: 12.5
  current_momentum: high        # high | medium | low | stalled

health: at_risk                 # on_track | at_risk | blocked | stalled
health_signals:
  - "Milestone MS-002 is at risk: 80% of time elapsed, 60% of work done"
  - "Dependency PRJ-003 is behind schedule"

outcome_statement: "A working executive reasoning engine that produces daily attention budgets, priority rankings, and decision briefs"
```

### Project lifecycle

```
                               ┌──────────┐
                               │  DRAFT   │  Idea, not yet committed
                               └────┬─────┘
                                    │ commitment to proceed
                                    ▼
                               ┌──────────┐
                    ┌──────────│  ACTIVE  │──────────┐
                    │          └────┬─────┘          │
                    │               │                │
                    ▼               ▼                ▼
              ┌──────────┐   ┌──────────┐    ┌──────────┐
              │  PAUSED  │   │AT RISK   │    │ STALLED  │
              │ (intend  │   │(needs    │    │(blocked, │
              │  resume)  │   │interven-)│    │inactive) │
              └────┬─────┘   │  tion)   │    └────┬─────┘
                   │         └──────────┘         │
                   │              │                │
                   └──────┬───────┘────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │COMPLETED │  Delivered outcome
                    └──────────┘
                          │
                          ▼
                    ┌──────────┐
                    │CANCELLED │  Decided not to pursue
                    └──────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ABANDONED │  No longer relevant, no intention
                    └──────────┘   to resume (distinct from cancelled)
```

**Lifecycle transitions are governed.** Each transition is logged as an observation (OBS-xxx) with rationale. Abandonment requires more justification than completion. Cancellation requires more than pausing.

### Project-Goal relationship

- Goals are **why**. Projects are **how**.
- A goal may spawn multiple projects over time.
- A project may serve multiple goals.
- Projects complete; goals evolve.
- The reflection system evaluates: "Did completing PRJ-001 actually advance GL-003?"

### Project-Attention relationship

Attention is allocated to projects, not goals. The attention manager operates at the project level:

| Project attention state | Meaning |
|---|---|
| Project is ACTIVE and attention is ACTIVE | Currently being worked on |
| Project is ACTIVE but attention is DORMANT | Active project that hasn't been touched recently (stall risk) |
| Project is PAUSED and attention is DORMANT | Intentionally deferred |
| Project is PAUSED and attention is FORGOTTEN | Deferred so long it's effectively abandoned |
| Project is COMPLETED | Attention released, archival |
| Project is ABANDONED | Attention released, occasional review for learning |

The attention manager monitors active projects for attention decay and surfaces stall warnings.

---

## 7. Revised Executive-Centric Architecture

### Center of gravity shift

**DOC-016 (Identity-Centric) flow:**
```
Persona -> Memory/Knowledge -> Reflection
```

The system answers: "What do I know about the operator?"

**Proposed (Executive-Centric) flow:**
```
Persona -> Attention -> Projects -> Decisions -> Actions
                                        │
                                        ▼
                                  Observations
                                        │
                                        ▼
                              Reflection (multi-cycle)
                                        │
                                        ▼
                            Updates Persona + Priorities
```

The system answers: "What should the operator focus on and do next?"

### Revised 8-layer architecture

DOC-004's 8-layer stack is preserved. The changes are in what each layer *does*.

```
┌──────────────────────────────────────────────────────────────────┐
│  8. EXPERIENCE LAYER                                             │
│  NEW BEHAVIORS:                                                  │
│  ● Attention budget display (what to focus on now)              │
│  ● Priority dashboard (ranked view of competing claims)          │
│  ● Decision support interface (decision briefs with context)     │
│  ● Project portfolio view (health, momentum, attention)          │
│  ● Reflection review (cycle outputs with decisions)              │
│  PRESERVED:                                                      │
│  ● Knowledge management interface                                │
│  ● Workflow oversight and approval                               │
│  ● Observability and audit dashboards                             │
│  ● System configuration                                          │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  7. DELIVERY AND AUTOMATION PLATFORM                             │
│  PRESERVED: existing                                             │
│  NEW: Projects can trigger delivery workflows                    │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  6. WORKFLOW AND AGENT RUNTIME                                   │
│  PRESERVED:                                                      │
│  ● Workflow execution (existing)                                 │
│  ● Audit logging (existing)                                      │
│  ● Human approval gates (existing)                               │
│  NEW CAPABILITIES:                                               │
│  ● EXECUTIVE REASONING ENGINE                                    │
│    └─ Signal detection, priority computation, decision support   │
│  ● ATTENTION MANAGER                                             │
│    └─ Attention state, decay, triggers, capacity, graph          │
│  ● REFLECTION ENGINE                                             │
│    └─ Multi-cycle orchestrator (daily/weekly/monthly/quarterly)  │
│  ● BACKGROUND SCHEDULER                                          │
│    └─ Continuous event loop, trigger evaluation, daemon mode     │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  5. ARCHITECTURE AND GOVERNANCE REPOSITORY                       │
│  PRESERVED: existing                                             │
│  NEW:                                                             │
│  ● Executive function governance (attention policies)            │
│  ● Reflection governance (cycle cadence, output standards)        │
│  ● Project governance (lifecycle policies)                       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  4. KNOWLEDGE AND PERSONAL CONTEXT PLATFORM                      │
│  PRESERVED:                                                      │
│  ● Knowledge store (existing — canonical + derived)              │
│  ● Observation store (from DOC-016)                              │
│  ● Goal store (from DOC-016)                                     │
│  ● Decision store (from DOC-016)                                 │
│  ● Preference / Belief / Habit (from DOC-016)                    │
│  NEW:                                                             │
│  ● Project store (PRJ entity lifecycle)                          │
│  ● Commitment register (CMT entity lifecycle)                    │
│  ● Risk inventory (RSK entity lifecycle)                         │
│  ● Constraint store (CON entity lifecycle)                       │
│  ● Focus area store (FCA entity lifecycle)                       │
│  ● Opportunity register (OPP entity lifecycle)                   │
│  ● Attention log (time-series attention state transitions)       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  3. MODEL GATEWAY                                                │
│  PRESERVED: existing (unchanged)                                 │
│  NEW CONSUMERS:                                                  │
│  ● Executive reasoning engine uses gateway for pattern detection │
│  ● Reflection engine uses gateway for multi-cycle analysis       │
│  ● Decision support uses gateway for context assembly            │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  2. IDENTITY, SECURITY, AND POLICY                               │
│  PRESERVED: existing                                             │
│  EXPANDED:                                                       │
│  ● Persistent persona now includes preferences, beliefs, values  │
│  ● Personal data policies govern observation/reflection data     │
│  ● Attention-bounded policy evaluation (respect focus mode)      │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────┐
│  1. PLATFORM FOUNDATIONS                                         │
│  PRESERVED: existing                                             │
│  NEW:                                                             │
│  ● Scheduler daemon for reflection cycles                        │
│  ● Attention manager persistence                                 │
└──────────────────────────────────────────────────────────────────┘
```

### New cross-cutting concern: Executive Context

Every layer above Layer 2 now carries **executive context** alongside identity context:

```
identity_context: who is making the request
executive_context: what is the current situation
  ├── current_focus: PRJ-042
  ├── active_projects: [PRJ-042, PRJ-038, PRJ-045]
  ├── attention_state: focused | fragmented | idle
  ├── energy_level: high | medium | low
  └── priority_ranking: [PRJ-042 > PRJ-038 > PRJ-045 > ...]
```

This context flows through all interactions, ensuring every component operates with awareness of what currently matters.

### Data flow (revised)

```
[Observation Stream] (continuous, from all sources)
        │
        ▼
[Executive Reasoning Engine] (continuous loop)
        │
        ├──► [Signal Detection] ──► What is happening?
        ├──► [Priority Computation] ──► What matters now?
        └──► [Decision Support] ──► What should I do?
                │
                ▼
        [Attention Manager] ──► Attention budget
                │
                ▼
        [Experience Layer] ──► Presented to operator
                │
                ▼
        [Operator Actions] ──► Decisions, focus shifts, completions
                │
                ▼
        [Observation Stream] ──► Feedback loop
                │
                ▼
        [Reflection Engine] (multi-cycle)
                │
                ├──► [Daily] ──► Tomorrow's budget
                ├──► [Weekly] ──► Priorities, patterns
                ├──► [Monthly] ──► Abandonment, strategy
                └──► [Quarterly] ──► Values, goals, learning
                        │
                        ▼
                [Persona Update]
                [Priority Revision]
                [Project Portfolio Adjustment]
```

---

## 8. Future-State Vision

### Three years from now

The system has accumulated years of observations, decisions, goals, projects, and reflections. It has learned how the operator thinks, what they value, and how they decide. Here is what it actually *does*.

---

### Daily: Before the operator asks

At 7:00 AM, the system presents, unprompted:

```
Good morning. Here is what I see.

YOUR DAY
────────
Focus: Architecture decision on PRJ-042
  │ You scheduled this yesterday morning.
  │ You make these decisions best before 11am (91% of past
  │ decisions of this type were made in your high-energy window).
  │ I've prepared a brief comparing Options A and B based on
  │ your past preferences and constraints.

Prep: Team sync at 10:00
  │ PRJ-038 status summary ready.
  │ The blocker you mentioned is still open; I've noted it
  │ as the first agenda item.

ATTENTION MANAGEMENT
────────────────────
Warning: PRJ-038 — 14 days without attention
  │ You committed to this by end of quarter.
  │ Deprioritize or reschedule? I recommend 2 hours on Wednesday.

Pattern: You deprioritized architecture work 3 times this month
when meetings filled your mornings. Tomorrow is clear.
Shall I block 9-11am for decision time?

SOMETHING CHANGED
─────────────────
PRJ-050: The API review you were waiting on just completed.
  │ This unblocks your next milestone.
  │ The reviewer's comments align with preferences you've
  │ expressed about similar systems.

DECISIONS TODAY
───────────────
1. PRJ-042: Option A vs Option B (due today)
   → I'd choose A. It matches every past decision of this type.
   → Confidence: 88%

2. PRJ-051: Accept the speaking invitation?
   → You've declined similar requests twice this year
   → But this topic aligns with your Q3 focus area
   → Recommend: accept, with conditions

3. CMT-022: Team dinner Thursday
   → You committed, but your energy pattern suggests Thursday
     evening is your lowest point
   → Recommend: attend but leave by 8pm
```

### Weekly: Pattern recognition

```
WEEKLY REVIEW
─────────────

Theme: "Integration debugging" (4th time this quarter with
integration-related theme)

PROJECTS
PRJ-042: On track ──── Decision made, advancing
PRJ-038: Stalled ───── 14 days, needs intervention
PRJ-045: Completed! ── Delivered 2 days early

DECISIONS: 14 this week
  12 routine — matched predicted choices
  2 significant — both matched values but one was faster
  than expected (you had relevant context from 8 months ago)

PATTERNS DETECTED
─────────────────
● Deep work peak: 9-11am (63% of effective output in 2 hours)
● Low point: 2-4pm (meetings scheduled here are least productive)
● You consistently push creative work to after 3pm, then
  deprioritize it. This week, 4 of 5 creative tasks were deferred.
  → Suggestion: schedule creative work for 9-11am.

COMMITMENTS
● CMT-015: Review deadline Friday — estimated 4h, best Wednesday
● CMT-018: Promised PRJ-050 feedback — 2h overdue

TENSION IDENTIFIED
──────────────────
You value "architecture quality" (PRS fact) but chose speed
over design review 3 times under deadline pressure.

You then spent 2x the saved time in rework each time.

This is a persistent pattern (detected 3 times this quarter).
Do you want to:
  (a) Accept the trade-off consciously
  (b) Adjust deadlines to include review time
  (c) Both

RISK UPDATE
───────────
PRJ-050: Dependency delay — partner team is behind
  → Impact: milestone slip of 1-2 weeks
  → Mitigation: parallel track available, recommended
  → I've prepared the parallel plan if you want to review it.
```

### Monthly: Strategic decisions

```
MONTHLY REVIEW
──────────────

PROJECT PORTFOLIO
Active: 5  │  At risk: 2  │  Stalled: 1  │  Completed: 3

Time allocation (actual vs intended):
  Planned:     PRJ-042 (40%)  PRJ-038 (25%)  PRJ-045 (20%)  ...
  Actual:      PRJ-042 (35%)  PRJ-038 (12%)  PRJ-045 (30%)  ...
  Gap:         PRJ-038 is under-attended. PRJ-045 over-attended
  (PRJ-045 was more interesting but lower priority)

ABANDONMENT RECOMMENDATIONS
───────────────────────────
PRJ-052: "Learn Rust" — 90 days without attention
  → Your past 3 attempts to learn languages followed the same pattern:
      2 weeks intensive, then abandonment
  → Recommendation: abandon formally. If interest resurfaces,
    start with a concrete project, not a "learn X" goal.

CONTINUE / PAUSE / ABANDON
──────────────────────────
PRJ-038: Pause recommended. Dependency has not resolved.
  → Next 30 days will not move this forward.
  → Suggested: revisit in September.
  → Save attention for PRJ-042 and PRJ-045.

BELIEF UPDATE
─────────────
Current: "I'm better at backend than frontend work"
Evidence: You completed 3 backend projects (on time) and
          2 frontend tasks (both delayed, both had rework)

BUT: The 2 frontend tasks were your first in this stack.
      Your rate of improvement on frontend is faster than
      your rate of improvement was on backend at the same stage.

Updated belief: "I'm less experienced at frontend, not worse"
  → Confidence: 65% (needs more data)
  → Implication: don't avoid frontend work; do account for
    learning curve in estimates.
```

### Quarterly: Learning extraction

```
QUARTERLY RETROSPECTIVE — Q2 2026
─────────────────────────────────

GOAL OUTCOMES
"Build identity-centric AIOS": 70% complete
  │ Trajectory: on track, slower than planned
  │ Cause: scope creep on PRJ-044 (added 2 sub-projects)
  │ Learning: I decompose poorly under optimism. Estimate
  │           ×1.5 when breaking down projects.

DECISION MODEL ACCURACY
  Technical decisions:  92% accurate (I know your technical
                        preferences well)
  People decisions:     40% accurate (new factors appear each time)
  Prioritization:       78% accurate (improving; was 68% last quarter)
  Overall:              76% → 82% (improvement trend)

  Lowest confidence: "Would you accept a speaking invitation?"
    → You said yes to 2 of 5 this year
    → Reason varies by topic alignment, not by time availability
    → New signal to track: topic alignment score

TENSIONS IDENTIFIED
───────────────────
1. Speed vs quality (3rd consecutive quarter)
   → You acknowledge this every quarter but patterns haven't changed
   → This may be a stable trade-off, not a tension to resolve
   → Recommendation: accept as a conscious choice, stop flagging

2. Exploration vs delivery
   → You started 3 new projects this quarter, completed 1
   → Starting feels productive; finishing is harder
   → Recommendation: limit active projects to 3 for Q3

LEARNING EXTRACTED
──────────────────
1. 24-hour cool-down improves decision quality
   → 88% of decisions made after 24h reflection were correct
   → 62% of decisions made immediately needed revision
   → Implemented: daily reflection flags same-day decisions for review

2. Frontend estimates are consistently 40% low
   → Buffer added: ×1.4 for frontend work (and improving)

3. Morning deep work is 3× more effective than afternoon
   → Attention manager now protects 9-11am automatically

4. I work better with constraints
   → Projects with tight deadlines: 89% completion rate
   → Projects with open timelines: 45% completion rate
   → Suggestion: always set a target date, even for exploratory work

PERSONA EVOLUTION
─────────────────
Values: Stable (autonomy, quality, simplicity unchanged)

Preferences changed:
  × "I prefer Python for data work"
  → "Python for data work, Rust for systems work"
  (Evidence: last 3 systems projects chosen in Rust)

Beliefs refined:
  × "I'm not good at frontend"
  → "I'm learning frontend and improving faster than I did at backend"

Habits detected (new):
  ● Morning review of email → leads to 30min context switching loss
    → Recommendation: defer email to 11am

NEXT QUARTER
────────────
Primary focus: Complete executive reasoning engine (PRJ-xxx)
Secondary: PRJ-045 (momentum is good, protect it)
Retire: PRJ-052 (formally abandon "Learn Rust" project)
New: PRJ-055 (speaking prep — matches Q3 focus area)
     → I notice this aligns with a pattern: you prepare
       more thoroughly than expected for speaking events
     → Suggested: 2-week preparation timeline (your past prep
       averaged 14 days for 30-min talks)

Pause: PRJ-038 (dependency unresolved, revisit September)
```

### What makes this not a chatbot

- **It initiates.** It never waits to be asked.
- **It notices.** It detects patterns the operator doesn't see.
- **It predicts.** It uses decision history to anticipate choices with measured confidence.
- **It suggests.** It proposes actions, not just summaries.
- **It protects.** It guards attention and respects boundaries.
- **It reflects.** It analyzes behavior and extracts learning.
- **It adapts.** It changes its understanding as the operator evolves.
- **It challenges.** It surfaces tensions between values and behavior.
- **It remembers what matters.** Not everything — just what's contextually relevant.
- **It forgets intentionally.** It manages forgetting as a cognitive function, not a failure.
- **It knows its limits.** It identifies areas of low confidence and asks for help.

### What makes this not a memory system

A memory system answers: "What happened?"

This system answers:
- "What should I do now?"
- "What am I missing?"
- "What pattern should I notice?"
- "What have I changed my mind about?"
- "What commitment am I at risk of breaking?"
- "What should I stop doing?"
- "What decision do I need to make today?"
- "What have I learned recently that I should remember?"
- "How has my thinking changed?"

### What makes this not an agent framework

An agent framework executes tasks it is given.

This system:
- **Reasons** about what tasks are worth doing
- **Prioritizes** among competing demands
- **Understands** the operator well enough to represent their judgment
- **Evolves** its understanding as the operator changes
- **Operates** continuously in the background
- **Surfaces** what matters rather than waiting for instructions

The final architecture is not an operating system for agents.

It is an operating system for a person.

---

## 9. Prioritized Roadmap

This roadmap assumes DOC-016's identity-centric foundation is being built in parallel. The items below are what come *after* — the executive function layer.

### Phase A: Project and Commitment Model

**Prerequisites:** Identity store, observation capture (from DOC-016)

| Item | Complexity | Description |
|---|---|---|
| Project schema + store | Low | PRJ entity, lifecycle, CLI (following DOC-016 patterns) |
| Commitment schema + store | Low | CMT entity, lifecycle, relation to projects |
| Project portfolio CLI | Low | List active, at-risk, stalled; filter by health |
| Observation→project linking | Low | Wire observations to project IDs at capture time |

**Why first:** Projects and commitments are the concrete objects the executive reasoning engine operates on. Without them, the reasoning engine has nothing to reason about.

---

### Phase B: Attention Manager

**Prerequisites:** Phase A, observation store populated

| Item | Complexity | Description |
|---|---|---|
| Attention state model | Medium | Active/dormant/forgotten/resurfaced with decay functions |
| Attention decay computation | Medium | Per-item λ values, decay function, threshold transitions |
| Trigger evaluation | Medium | Time, event, and pattern-based trigger conditions |
| Attention graph (dependencies) | Medium | Track blocked-by, blocks, related between items |
| Fragmentation detection | Low | Alert when active > 3 or dormant > 15 |
| Attention budget output | Medium | Recommended focus allocation for current period |
| Attention log (time-series) | Low | Record all attention state transitions as observations |

**Why second:** The attention manager is the core executive function. It determines what matters *now*, which every other function depends on.

---

### Phase C: Executive Reasoning Engine

**Prerequisites:** Phase B, model gateway integration

| Item | Complexity | Description |
|---|---|---|
| Signal detection (urgency, momentum, pattern) | Medium | Scan inputs for signals demanding attention |
| Priority computation engine | High | Weighted scoring combining urgency, importance, commitment, momentum, energy |
| Decision context assembly | Medium | Retrieve similar past decisions, preferences, constraints |
| Action recommendation generation | Medium | Produce ranked suggestions (do now, today, delegate, deprioritize, abandon) |
| Attention budget display | Low | Generate formatted morning brief (see Section 8) |
| Continuous evaluation loop | Medium | Run reasoning engine continuously, not on demand |

**Why third:** The reasoning engine depends on the attention manager for state and the model gateway for AI-assisted reasoning.

---

### Phase D: Reflection Engine (Multi-Cycle)

**Prerequisites:** Phase C, sufficient observation history (30+ days)

| Item | Complexity | Description |
|---|---|---|
| Daily reflection cycle | Medium | End-of-day reconstruction, comparison, projection |
| Weekly reflection cycle | Medium | Pattern detection, momentum assessment, tension identification |
| Monthly reflection cycle | High | Strategic alignment, resource allocation, abandonment analysis |
| Quarterly reflection cycle | High | Outcome analysis, decision audit, value check, learning extraction |
| Reflection→Persona updates | Medium | Wire reflection outputs to Persona changes (preferences, beliefs, values) |
| Reflection→Priority updates | Medium | Wire reflection outputs to priority recomputation |

**Why fourth:** Reflection depends on accumulated observation data. It should not be introduced until there is enough data to reflect on meaningfully (at least one month of observations).

---

### Phase E: Risk, Opportunity, Constraint

**Prerequisites:** Phase C (needs the reasoning engine to contextualize these)

| Item | Complexity | Description |
|---|---|---|
| Risk schema + store | Low | RSK entity with probability, impact, status, mitigation |
| Opportunity schema + store | Low | OPP entity with source, relevance, pursue criteria |
| Constraint schema + store | Low | CON entity with type, scope, severity |
| Risk detection (from patterns) | Medium | Wire reflection pattern detection to risk creation |
| Opportunity detection (from patterns) | Medium | Wire reflection to opportunity surfacing |
| Constraint-aware reasoning | Medium | Include constraints in priority computation |

**Why fifth:** These are refinements on the core executive model. They add depth but aren't required for the initial reasoning engine to function.

---

### Phase F: Energy and Context Model

**Prerequisites:** 90+ days of observation data

| Item | Complexity | Description |
|---|---|---|
| Energy pattern learning | Medium | Detect high/low energy periods from observation history |
| Energy-aware scheduling | Medium | Match task type to energy level in attention budget |
| Context computation | Medium | Compute current context from active projects, focus area, recent decisions |
| Context flow through all layers | Medium | Wire executive context into all component interactions |

**Why sixth:** Energy and context require sufficient historical data to detect meaningful patterns. Introducing them too early produces noisy recommendations.

---

### Phase G: Proactive Behavior

**Prerequisites:** All prior phases, system trust established (operator has experienced value)

| Item | Complexity | Description |
|---|---|---|
| Background scheduler daemon | Medium | Continuous event loop for the executive reasoning engine |
| Trigger-based notifications | Medium | Attention alerts, commitment warnings, opportunity surfaced |
| Morning brief generation | Medium | Daily proactive summary (see Section 8 example) |
| Pattern-contrast alerts | High | "You're doing X differently than usual" |
| Decline detection | High | "You've deprioritized this 3 times — should we abandon it?" |

**Why seventh:** Proactive behavior is the most invasive capability. It should be introduced last, after the underlying reasoning is accurate enough to be trusted, and after the operator has experienced enough value to accept proactive suggestions.

---

## Related artifacts

- [DOC-004 — Target Architecture](architecture/target-architecture.md) — 8-layer architecture extended by this analysis
- [DOC-005 — Capability Map](architecture/capability-map.md) — capabilities to be extended with executive function capabilities
- [DOC-008 — Traceability Standard](governance/traceability-standard.md) — identifier conventions for new entities
- [DOC-010 — Minimal Viable Ontology](ontology/minimal-viable-ontology.md) — ontology to be extended with project, commitment, risk, opportunity, constraint
- [DOC-016 — Identity-Centric Pivot Analysis](architecture/identity-centric-pivot-analysis.md) — predecessor analysis this document critiques and extends
- [ADR-004 — Identity Model](adr/0004-identity-model.md) — current identity decision, foundation for the persona model

---

## What this document does not do

This document is an analysis, not a decision. It identifies conceptual gaps in the identity-centric pivot and proposes directions for executive function. Each significant change requires its own ADR with documented context, options, rationale, and consequences.

This document does not replace DOC-016. The identity-centric foundation (persona, observation, goal, decision) is the prerequisite for the executive-centric layer proposed here. Both are needed.

This document does not propose a rewrite. Every existing component — knowledge platform, model gateway, workflow runtime, ADR process, capability map, traceability standard — is preserved. The executive function layer is additive, running on top of the existing foundation.
