# Observation Capture Strategy

**ID:** DOC-008
**Status:** Draft
**Last reviewed:** 2026-06-10
**Parent:** ADR-008, CAP-012

---

## Purpose

Define the detailed capture mechanisms, integration architecture, deduplication logic, retention policy, and implementation priorities for the observation store (ADR-008). This document serves as the design reference for building capture sources and does not reopen decisions made in ADR-008.

---

## 1. Capture architecture overview

Observations enter the store through three independent paths (ADR-008 Part 1):

```
┌─────────────────┐    ┌──────────────────┐    ┌───────────────────┐
│  Layer A        │    │  Layer B          │    │  Layer C           │
│  Automatic      │    │  Low-friction     │    │  Scheduled         │
│  (no effort)    │    │  manual           │    │  reflection        │
├─────────────────┤    ├──────────────────┤    ├───────────────────┤
│ workflow events │    │ cli: aios observe │    │ end-of-day prompt  │
│ gateway calls   │    │ hotkey capture    │    │ end-of-week prompt │
│ filesystem      │    │ terminal hook     │    │ end-of-month       │
│ calendar        │    │ contextual prompt │    │ prompt             │
│ git events      │    │                   │    │                    │
│ browser         │    │                   │    │                    │
│ application     │    │                   │    │                    │
│ focus           │    │                   │    │                    │
└────────┬────────┘    └────────┬─────────┘    └─────────┬──────────┘
         │                     │                         │
         └─────────────────────┴─────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Deduplication     │
                    │   (content+context  │
                    │    hash, 5-min      │
                    │    window)          │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Quality gate      │
                    │   (sampling,        │
                    │   confidence check) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Observation store │
                    │   (file-based,      │
                    │   by-date)          │
                    └─────────────────────┘
```

---

## 2. Layer A — Automatic capture sources

### 2.1 Workflow execution events

**Mechanism:** The workflow executor (Layer 6a) emits an observation for every workflow step. Workflow runs generate observations at start, completion, and for each step. Approval gate events (requested, granted, denied) are also captured.

**Schema mapping:**
- `type`: `action` or `completion`
- `source.mechanism`: `auto`
- `source.component`: `workflow`
- `source.id`: workflow run ID (e.g., `WR-20260610-NNN`)
- `content.summary`: `"Workflow XYZ step N: description"`
- `context.project`: PRJ-ID from workflow definition
- `quality.confidence`: `auto`

**Implementation:** Embed observation emission in the workflow executor's step lifecycle hooks. Each step completion callback writes an observation to the store asynchronously.

### 2.2 Model gateway calls

**Mechanism:** The model gateway (Layer 3) emits an observation for each API call. This provides an automatic record of when and why models were queried.

**Schema mapping:**
- `type`: `action`
- `source.mechanism`: `auto`
- `source.component`: `gateway`
- `source.id`: gateway request ID
- `content.summary`: `"Model call: {model} on behalf of {caller}"`
- `content.detail`: `"{tokens} tokens, ${cost}, {duration}s"`
- `quality.confidence`: `auto`

**Implementation:** Gateway middleware intercepts responses and writes observations. This is the lowest-friction capture because it requires no operator action and no new infrastructure.

### 2.3 Calendar integration

**Mechanism:** Local calendar integration reads structured calendar data from the local calendar store and generates observations for events that occurred. VEVENTs rendered as observations with start, end, summary, and description.

**Schema mapping:**
- `type`: `event`
- `source.mechanism`: `auto`
- `source.component`: `calendar`
- `source.id`: calendar event UID
- `content.summary`: calendar event summary
- `content.detail`: calendar event description (optional)
- `quality.completeness`: `medium` (calendar events are structured but may not reflect actual attendance)

**Implementation:** Poll-based: read calendar file (e.g., iCalendar `.ics`, or caldav-compatible server) at configurable intervals. Only events in the past (completed events) generate observations. Future events are not observations — they are commitments.

### 2.4 Filesystem events

**Mechanism:** Watch specified directories for file create/modify/delete events. Knowledge assets, governance documents, and project files generate observations when changed.

**Schema mapping:**
- `type`: `event`
- `source.mechanism`: `auto`
- `source.component`: `filesystem`
- `source.id`: file inode or path
- `content.summary`: `"File {path} created/modified"`

**Implementation:** Use inotify (Linux) or Watchdog (cross-platform Python) to watch configured directories. Debounce rapid events (save spamming) within a 30-second window.

### 2.5 Git events

**Mechanism:** Track git activity — commits, branches, PRs — for repositories under observation.

**Schema mapping:**
- `type`: `action` (commit) or `completion` (merge, PR close)
- `source.mechanism`: `auto`
- `source.component`: `git`
- `source.id`: commit hash or PR number
- `content.summary`: commit message or PR title
- `context.project`: PRJ-ID inferred from repository → project mapping

**Implementation:** Git hooks (`post-commit`) or polling `git log` for new entries. Repository-to-project mapping must be configured.

### 2.6 Browser activity (optional)

**Mechanism:** Optional browser extension captures visited URLs, search queries, and time spent per domain. This is the highest-risk capture source due to privacy and noise concerns.

**Schema mapping:**
- `type`: `event`
- `source.mechanism`: `auto`
- `source.component`: `browser`
- `content.summary`: visited URL or search query
- `quality.confidence`: `auto`
- `quality.completeness`: `low` (browser captures intent poorly)

**Implementation:** Browser extension sends events to a local HTTP endpoint. Sampling rate is configurable (default: 1 in 10 events). Users can pause all browser capture at any time via the extension popup.

### 2.7 Application focus tracking (optional)

**Mechanism:** Track which application window has focus and for how long. This provides context for what the operator was doing between explicit captures.

**Schema mapping:**
- `type`: `event`
- `source.mechanism`: `auto`
- `source.component`: `focus`
- `content.summary`: `"Active: {application name}"`
- `content.detail`: `"{window title}"`

**Implementation:** Linux: `xdotool` or `i3-msg` polling. macOS: Accessibility API. Windows: Win32 API. Poll interval: 60 seconds. Only records transitions (same app for >5 min).

---

## 3. Layer B — Low-friction manual capture

### 3.1 CLI command

**Prototype:**
```bash
aios observe "did X" --project PRJ-042 --energy medium --tags review,design
```

The CLI command writes directly to the observation store. It is the simplest capture mechanism and the one that should ship first.

**Schema mapping:**
- `type`: Defaults to `note`; `--type` flag overrides to `decision`, `completion`, etc.
- `source.mechanism`: `manual`
- `source.component`: `cli`
- `source.id`: operator name
- `content.summary`: positional argument
- `content.detail`: `--detail` flag
- `context.project`: `--project` flag
- `energy`: `--energy` flag
- `quality.confidence`: `operator_verified`

### 3.2 Hotkey capture

**Mechanism:** System-wide hotkey opens a minimal input dialog (zenity, dmenu, or terminal popup). Operator types a one-line observation and optionally selects a project. The observation is captured with zero context switch.

**Implementation:** Two variants:
- **GUI:** Hotkey → dmenu/rofi → text input → submit writes to observation store
- **Terminal:** Hotkey → terminal overlay → text input → submit

The hotkey captures focus app (via application focus tracking) and includes it as context.

### 3.3 Terminal hook

**Mechanism:** A terminal command (`aios-obs`) captures the previous shell command and its output as an observation context. For example:
```bash
$ python tests/run_suite.py
... test output ...
$ aios-obs "ran test suite, all passing"
```
The hook would capture: `"ran test suite, all passing"` with the previous command (`python tests/run_suite.py`) appended as context.

**Implementation:** Shell function that reads `$?`, `!!` (previous command), and the most recent terminal output (if available), then writes an observation with the operator's appended note.

### 3.4 Contextual workflow prompt

**Mechanism:** When a workflow completes, the runtime displays an optional prompt:
```
Workflow WF-006 completed successfully.
Anything to note? (press Enter to skip)
> 
```

This captures the operator's reflection immediately after an action, when context is freshest.

**Implementation:** Optional interactive step in the workflow executor's completion handler.

---

## 4. Layer C — Scheduled reflection prompts

### 4.1 End-of-day prompt

**Timing:** Configurable time (default: 20:00 local time). If the operator is active, a notification is sent. If no response within 30 minutes, it expires silently.

**Prompt:** `"What was the most important thing that happened today?"`

**Processing:** The response becomes an observation of type `note` with source `scheduled`. If no response, a flag is set to indicate the prompt was skipped but does not create an empty observation.

### 4.2 End-of-week prompt

**Timing:** Configurable (default: Friday 18:00). Links to the week's observations for review.

**Prompt:** `"What pattern stood out this week?"`

**Optional:** Links to daily aggregates for the past 7 days to help the operator recall.

### 4.3 End-of-month and quarterly prompts

These are heavier prompts that may integrate with the reflection engine (Phase 7). They should produce a decision, not just a note. These are deferred until the reflection engine is operational.

---

## 5. Deduplication logic

### 5.1 Deduplication key

The deduplication key (ADR-008 Part 2) is computed at capture time:

```
duplicate_key = hash(
    observation.timestamp truncated to 5-minute window +
    observation.type +
    observation.source.component +
    observation.source.id (when available) +
    observation.content.summary (truncated to 256 chars, normalized)
)
```

### 5.2 Deduplication window

5 minutes. If an observation with the same key exists within the window, the new observation is either:
- **Discarded** (identical content): dropped silently
- **Merged** (count incremented): for automatic events that occur multiple times in the window (e.g., gateway calls), a counter is incremented rather than storing duplicate rows

### 5.3 Threshold adjustments

- Automatic sources: deduplication window applies strictly
- Manual sources: deduplication is a warning, not a block (operator may be noting the same thing deliberately)
- Scheduled sources: no deduplication (each prompt is unique by timestamp)

---

## 6. Retention and archival

| Retention period | Granularity | Action |
|---|---|---|
| 0–90 days | Full granularity | All observations retained at original schema |
| 91–365 days | Daily aggregates | Observations compressed: per-day, per-source, per-project summaries retained with aggregate counts and key content |
| >365 days | Monthly summaries | Observations compressed to monthly aggregates: total counts, top sources, summary of observation content |

**Exemptions:**
- Operator-declared `note` type observations are exempt from automatic compression
- Observations tagged `requires_review: true` are exempt until reviewed

---

## 7. Implementation priorities

| Priority | Component | Dependencies | Phase |
|---|---|---|---|
| P0 | CLI: `aios observe` | Observation store filesystem location | Phase 5 |
| P0 | Observation store (file-based, write) | ADR-003 pattern, directory structure | Phase 5 |
| P1 | Workflow execution events | Workflow executor (existing Layer 6a) | Phase 5 |
| P1 | Model gateway call events | Model gateway (existing Layer 3) | Phase 5 |
| P2 | Scheduled end-of-day prompt | Timer service (Layer 6b) | Phase 6 |
| P2 | Terminal hook | CLI installed, shell config | Phase 6 |
| P3 | Git events | Git hooks | Phase 6 |
| P3 | Hotkey capture | Background daemon (Layer 6b) | Phase 6 |
| P4 | Filesystem events | Watchdog library | Phase 7 |
| P4 | Calendar integration | Calendar data source access | Phase 7 |
| P5 | Browser extension | Browser API | Phase 7 |
| P5 | Application focus tracking | Platform-specific APIs | Phase 7 |

---

## 8. File-based store layout

Observations are stored by date following ADR-003 patterns, in a dedicated observation directory:

```
platform/knowledge/observations/
  YYYY/
    MM/
      YYYY-MM-DD.yaml        # Observations for a single day
      YYYY-MM-DD.aggregated   # Aggregate for days >90 days old
```

Each observation file is a YAML document with a list of observations:

```yaml
date: 2026-06-10
observations:
  - id: OBS-20260610-001
    timestamp: "2026-06-10T09:15:00+02:00"
    type: action
    source:
      mechanism: auto
      component: gateway
      id: GW-20260610-R001
    content:
      summary: "Model call: gpt-4 on behalf of wr-002"
      detail: "1024 tokens, $0.02, 3.2s"
    context:
      project: PRJ-042
    quality:
      confidence: auto
```

---

## 9. Related artifacts

- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md) — architectural decision this document implements
- [CAP-012 — Observation and Capture](../architecture/capability-map.md) — capability served by this design
- [DOC-017 — Executive Cognition Analysis](executive-cognition-analysis.md) — analysis identifying the capture problem as critical
- [DOC-016 — Identity-Centric Pivot Analysis](identity-centric-pivot-analysis.md) — predecessor analysis
- [DOC-018 — Pivot Readiness Assessment](pivot-readiness-assessment.md) — peer review that identified the capture problem
- [ADR-003 — Knowledge Persistence Approach](../adr/0003-knowledge-persistence-approach.md) — storage pattern reused
