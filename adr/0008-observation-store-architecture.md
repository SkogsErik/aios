# 0008 — Observation Store Architecture

**ID:** ADR-008
**Status:** Accepted
**Date:** 2026-06-10
**Affects:** CAP-001, CAP-009, THEME-002, THEME-006
**Supersedes:** N/A
**Superseded by:** N/A

---

## Context

The entire identity, persona, and executive reasoning system (DOC-016, DOC-017) depends on a continuous stream of observations — timestamped records of decisions, actions, events, and notes. Every component of the executive cognition architecture relies on observations as input:

- **Attention manager** uses observation recency to compute attention decay
- **Executive reasoning engine** uses observation patterns for signal detection
- **Reflection engine** uses accumulated observations for pattern synthesis across daily/weekly/monthly/quarterly cycles
- **Preference learning** uses observation history to detect behavioral patterns
- **Decision modeling** uses past decision observations to predict future choices

The hard problem is not storage. The hard problem is **capture** — generating a sufficient volume and quality of observations with low enough friction that the operator does not abandon the practice.

Prior experience from personal knowledge management systems (Roam, Obsidian, Day One) demonstrates a well-understood failure mode: tools that require deliberate logging produce sparse, irregular data. Tools that passively capture produce dense, low-quality data. Neither alone is sufficient.

This ADR addresses both the capture architecture and the storage architecture for observations.

---

## Decision

### Part 1: Passive capture architecture

Observations are captured through three mechanisms operating simultaneously:

**Layer A — Automatic capture (no operator effort):**
- Workflow execution events (every workflow step executed becomes an observation, with step ID, status, duration, output)
- Model gateway calls (every model gateway call becomes an observation, with caller ID, model, tokens, cost)
- File system events (watched directories — new/updated knowledge assets generate observations)
- Calendar integration (events from local calendar generate observations)
- Git events (commits, PRs, branch activity generate observations)
- Browser activity (configurable — URLs visited, search queries, via optional browser extension)
- Application focus tracking (which application has focus, configurable granularity)

**Layer B — Low-friction manual capture:**
- CLI command: `aios observe "did X" --project PRJ-042 --energy medium`
- Quick-capture hotkey (configurable system-wide shortcut that opens a minimal capture prompt)
- Terminal hook: `aios-obs` command that captures the previous command and its output as an observation
- Contextual capture: when completing a workflow, the runtime prompts "anything to note?"

**Layer C — Scheduled reflection capture:**
- End-of-day prompt: "What was the most important thing that happened today?"
- End-of-week prompt: "What pattern stood out this week?"
- These prompts are themselves observations, and the responses are captured as observation content.

### Part 2: Observation deduplication

Observations are deduplicated at capture time using a content + context hash:

```python
duplicate_key = hash(
    observation.timestamp_window(5 minutes) +
    observation.type +
    observation.source +
    observation.content_hash
)
```

If an identical observation exists within the deduplication window, it is discarded or merged (count incremented) rather than stored separately.

### Part 3: Observation schema and storage

Observations follow the same file-based storage pattern as knowledge assets (ADR-003) but are organized by date for temporal query efficiency.

```yaml
# Schema: Observation
id: OBS-YYYYMMDD-NNN        # Date-prefixed sequential ID
timestamp: ISO8601            # When the observation occurred
type: action | decision | event | note | completion
status: active                # active | reviewed | superseded | archived

source:
  mechanism: auto | manual | scheduled
  component: workflow | gateway | calendar | git | cli | browser | operator
  id: string                  # Source-specific identifier (workflow run ID, etc.)

content:
  summary: string             # Short human-readable description
  detail: string              # Optional longer description or notes

context:
  project: PRJ-NNN | null     # Related project
  goal: GL-NNN | null         # Related goal
  decision: DEC-NNN | null    # Related decision
  commitment: CMT-NNN | null  # Related commitment
  tags: [string]

quality:
  confidence: auto | operator_verified | ai_suggested
  completeness: high | medium | low
  requires_review: bool       # Flag for reflection cycles

energy: high | medium | low | null   # Optional energy context
```

### Part 4: Retention and archival

- Raw observations are retained for 90 days at full granularity
- After 90 days, observations are summarized into daily/weekly aggregates (lossy compression)
- After 365 days, aggregates are further compressed to monthly summaries
- Operator-declared "note" type observations are exempt from automatic compression
- All compression is reversible from backup

### Part 5: Quality threshold

Not every event becomes an observation. The quality gate:

- **Automatic observations** from workflows, gateway calls, and git events are always captured (they are structured and high-confidence)
- **Automatic observations** from browser activity and application focus are sampled (1 in N events, configurable N)
- **Manual observations** have no quality threshold — the operator decides what matters
- **AI-suggested observations** (pattern-derived) require operator confirmation before becoming observations

---

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Multi-layer capture with file store (this decision)** | Addresses the behavior change problem explicitly; deduplication prevents noise; quality thresholds manage volume; file-based store is inspectable | Requires calendar, git, browser integrations; deduplication adds complexity |
| **Pure manual capture (CLI only)** | Simplest to implement; zero passive infrastructure | Will produce sparse, irregular data; fails the behavior change test; identity model will have no fuel |
| **Pure automatic capture** | Rich data with no operator effort | Produces high-volume low-quality data; overwhelming for reflection; operator has no agency over what is captured |
| **Relational database** | Faster queries; temporal indexing built-in | Binary format not inspectable; violates local-first inspection principle; inconsistent with ADR-003 |
| **No observation store (use knowledge store)** | No new store | Knowledge store is designed for curated documents, not high-volume temporal data; lifecycle mismatch; query pattern mismatch |

---

## Rationale

The multi-layer capture approach was chosen because:

- **The behavior change problem is the hard problem.** No amount of storage architecture solves it. The capture design must be the primary focus, with storage as a secondary concern.

- **Three layers compensate for each other's weaknesses.** Automatic capture provides volume. Manual capture provides quality and intentionality. Scheduled capture ensures reflection even when both are neglected.

- **File-based storage by date** enables simple temporal queries (list observations for a given day) without requiring a database. The existing knowledge store patterns (front-matter, version-controlled, inspectable) are preserved.

- **Deduplication prevents the most common failure** of automatic capture: noisy duplicate events that drown out signal.

- **Retention policy prevents indefinite accumulation** while preserving the ability to recover from backup.

---

## Consequences

**Positive:**
- Observation capture does not depend on operator discipline alone — three layers ensure data flows even when manual logging is inconsistent.
- Deduplication prevents observation noise from overwhelming the signal.
- Retention policy bounds storage growth and prevents stale data from degrading inference quality.
- File-based by-date storage is inspectable, portable, and consistent with ADR-003.

**Negative:**
- Calendar, file system, git, and browser integrations must be built — these are non-trivial and platform-specific.
- Deduplication logic must be carefully designed to avoid discarding legitimate distinct observations.
- Retention policy means older observations are aggregated, which may lose granularity needed for some analyses.

**Neutral:**
- The observation store sits alongside the knowledge store in Layer 4. They are separate stores with different organization (date-based vs domain-based).
- The capture architecture is independent of the storage architecture — capture mechanisms can be added or removed without changing the schema.

---

## Risks

| Risk | Mitigation |
|---|---|
| Automatic capture generates too much noise | Configurable sampling rate; deduplication window; quality thresholds |
| Manual capture never happens | Scheduled reflection prompts compensate; automatic capture provides baseline data |
| Calendar/git integrations fail or change | Integrations are optional; observation capture degrades gracefully without them |
| Deduplication discards distinct observations | Conservative deduplication window (5 minutes); operator can disable per-source |
| Observation volume exceeds file store capacity | Retention policy bound; file store scales to tens of thousands comfortably for personal use |

---

## Related artifacts

- [ADR-003 — Knowledge Persistence Approach](0003-knowledge-persistence-approach.md) — storage pattern reused for observations
- [DOC-016 — Identity-Centric Pivot Analysis](../architecture/identity-centric-pivot-analysis.md) — analysis requiring observations
- [DOC-017 — Executive Cognition Analysis](../architecture/executive-cognition-analysis.md) — analysis requiring observations for every component
- [DOC-018 — Pivot Readiness Assessment](../architecture/pivot-readiness-assessment.md) — peer review that identified the capture problem as the hardest unsolved issue
