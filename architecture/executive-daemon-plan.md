# Executive Daemon Implementation Plan

**ID:** DOC-010
**Status:** Draft
**Last reviewed:** 2026-06-10
**Parent:** ADR-010, ADR-009

---

## 1. Purpose

Define the implementation scope, CLI interface, event loop architecture, and first capture integration for the executive daemon (ADR-010 Layer 6b). This document covers the first working version only — a running daemon that observes real activity and surfaces at least one actionable pattern.

---

## 2. Scope (First Working Version)

| Capability | Included | Notes |
|---|---|---|
| Daemon process | Yes | Background process with PID management |
| CLI: `aios start` | Yes | Launch daemon in background |
| CLI: `aios stop` | Yes | Graceful shutdown via PID |
| CLI: `aios status` | Yes | Health, uptime, cycle count, state summary |
| CLI: `aios observe` | Yes | Manual observation capture |
| CLI: `aios patterns` | Yes | List recent pattern candidates |
| CLI: `aios pattern <id>` | Yes | Show single pattern detail |
| Git capture (poll) | Yes | `git log` polling for new commits |
| Attention decay | Yes | From existing `attention_manager.py` |
| Stall detection | Yes | From existing `rules_engine.py` |
| Priority scoring | Yes | From existing `rules_engine.py` |
| Pattern detection | Yes | Behavioral bias + preference divergence |
| Observation store | Yes | File-based (ADR-003 pattern) |
| Pattern store | Yes | From existing `stores.py` |
| Calendar capture | No | Phase 7 |
| Filesystem capture | No | Phase 7 |
| Browser capture | No | Deprioritized |
| AI reasoning (Layer 2) | No | Phase 7; model integration |
| Reflection engine | No | Phase 7 |

---

## 3. CLI interface

```
aios start                     Start daemon in background
aios stop                      Stop daemon (graceful)
aios status                    Show daemon status
aios observe <text>            Capture a manual observation
  --project PRJ-xxx            Associate with a project
  --energy high|medium|low     Energy context
  --tags tag1,tag2             Tags
aios patterns                  List recent pattern candidates
  --days 30                    Lookback window (default: 7)
  --status candidate|active    Filter by status
aios pattern <id>              Show pattern candidate detail
  --accept                     Accept the pattern
  --reject                     Reject the pattern
  --dismiss                    Dismiss the pattern
```

### Command routing

All commands route through a single `cli.py` entry point. Subcommands that require the daemon to be running (`status`, `patterns`, `pattern`) check for a PID file and return an error if the daemon is not running.

---

## 4. Event loop architecture

```
┌────────────────────────────────────────────┐
│  Event Loop (every CYCLE_SECONDS)          │
│                                            │
│  1. git_capture.poll()                     │
│     → new commits → Observation records    │
│     → observation_store.save()             │
│                                            │
│  2. attention_mgr.evaluate_all()           │
│     → state transitions (active/dormant)   │
│     → attention_store.save()               │
│                                            │
│  3. stall_detector.find_stalled()          │
│     → stall alerts                         │
│                                            │
│  4. deadline_scorer.score()                │
│     → deadline warnings                    │
│                                            │
│  5. priority scoring                       │
│     → ranked priority list                 │
│                                            │
│  (If scheduled cycle, every SCHEDULE_N):   │
│  6. pattern detection                      │
│     → behavioral_bias.detect()             │
│     → learning_engine.reconcile()          │
│     → candidate generation                 │
│     → pattern_store.save()                 │
│                                            │
│  7. state checkpoint                       │
│     → daemon_state.save()                  │
└────────────────────────────────────────────┘
```

### Timing

| Parameter | Default | Configurable |
|---|---|---|
| `CYCLE_SECONDS` | 300 (5 min) | Via env `AIOS_CYCLE_SECONDS` |
| `SCHEDULE_N` | 12 (every hour) | Via env `AIOS_SCHEDULE_N` |
| `GIT_POLL_DEPTH` | 50 commits | Via env `AIOS_GIT_POLL_DEPTH` |

### State checkpointing

Daemon state is serialized to `platform/knowledge/daemon/state.yaml` every cycle:

```yaml
last_run: 2026-06-10T14:30:00
cycle_count: 42
last_git_commit: abc123def456
attention_state: [...]
priority_ranking: [...]
stores:
  observation: platform/knowledge/observations/
  pattern: platform/knowledge/patterns/
  contradiction: platform/knowledge/contradictions/
```

---

## 5. Git observation capture

### Mechanism

Poll-based: run `git log --oneline --after=<last_seen> -<depth>` in a configured repository directory. Each new commit becomes an observation.

### Configuration

```yaml
# platform/knowledge/daemon/config.yaml
git:
  repos:
    /home/jck/AI/Development/aios:
      project: PRJ-000        # Default project mapping
      tag_prefix: "aios-"     # Commits with this prefix → observations
```

### Observation schema for git commits

```yaml
id: OBS-20260610-042
timestamp: 2026-06-10T14:22:00+02:00
type: action
source:
  mechanism: auto
  component: git
  id: abc123def456
content:
  summary: "feat: add git observation capture"
  detail: "Author: Erik\nFiles: 5 changed\nInsertions: 120, Deletions: 30"
context:
  project: PRJ-000
  tags: [git, commit]
quality:
  confidence: auto
  completeness: high
```

---

## 6. First pattern: behavioral bias

The first pattern surfaced by the daemon uses the `BehavioralBiasDetector` from `pattern_detector.py`:

1. After >= 3 capture cycles, aggregate observations by project per window
2. If no declared weights exist, use `weight_a = weight_b = 0.5` (neutral default)
3. Detect when one project receives > 60% of attention across >= 60% of windows
4. Generate candidate: "Your attention is concentrated on PRJ-xxx. Would you like to declare a priority weight for this project?"

This is deliberately simple — it proves the pipeline end-to-end without requiring the operator to declare values first.

---

## 7. File layout

```
platform/executive-daemon/
  __main__.py              # python -m executive-daemon entry point
  requirements.txt         # Dependencies (pyyaml)
  src/
    __init__.py
    cli.py                 # CLI dispatcher (aios)
    daemon.py              # Event loop, process lifecycle
    capture/
      __init__.py
      git_capture.py       # Git polling
    daemon_state.py        # State persistence, config loading
    attention_manager.py   # (existing)
    rules_engine.py        # (existing)
    learning_engine.py     # (existing)
    pattern_detector.py    # (existing)
    stores.py              # (existing)
  tests/
    ...
```

---

## 8. Related artifacts

- [ADR-010 — Runtime Model Evolution](../adr/0010-runtime-model-evolution.md) — two-runtime model requiring this daemon
- [ADR-009 — Executive Reasoning Engine Pattern](../adr/0009-executive-reasoning-engine-pattern.md) — Layer 1 rules engine design
- [ADR-008 — Observation Store Architecture](../adr/0008-observation-store-architecture.md) — observation schema and capture layers
- [DOC-004 — Target Architecture](../architecture/target-architecture.md) — Layer 6b executive daemon
- [CAP-013 — Executive Function](../architecture/capability-map.md) — capability served by this implementation
