# Executive Daemon

The executive daemon is Runtime B of the two-runtime model (ADR-010). It runs as a persistent background process providing the identity/executive layer of AIOS: attention management, rules-based priority scoring, pattern detection, and learning.

---

## Architecture

```
capture → attention → rules → pattern detection
           (every N seconds, default 300)
```

- **Layer 1** (ADR-009): Deterministic rules — always-on, no AI, sub-second latency
- **Layer 2** (ADR-009): AI-assisted inference — scheduled, review-gated
- State persisted atomically to `platform/knowledge/daemon/state.yaml`
- PID file at `/tmp/aios-daemon.pid`

---

## Setup

**Requirements:** Python 3.11+, system packages

```bash
cd platform/executive-daemon
pip3 install --break-system-packages -r requirements.txt
```

---

## Running Tests

```bash
cd platform/executive-daemon
PYTHONPATH=src python3 -m pytest tests/test_project_store.py \
  tests/test_rules_engine.py tests/test_attention_manager.py \
  tests/test_learning_engine.py tests/test_pattern_detector.py \
  tests/test_stores.py -q
```

> Note: `test_daemon.py` and `test_cli.py` start the daemon process and may hang in some CI environments. Run them separately with a timeout.

---

## CLI Reference

Run all commands from the repository root (paths resolve automatically).

### Daemon lifecycle

```bash
python3 platform/executive-daemon/src/cli.py start     # start background daemon
python3 platform/executive-daemon/src/cli.py stop      # stop daemon
python3 platform/executive-daemon/src/cli.py status    # show status + cycle stats
```

### Observations

```bash
aios observe "Spent 3h in flow state on the learning engine"
aios observe "Distracted all morning" --energy low --project PRJ-001
aios observe "Pair session with team" --tags collab,social --project PRJ-002
```

### Patterns

```bash
aios patterns               # last 7 days
aios patterns --days 30     # last 30 days
aios pattern CND-20260610-001 --accept
aios pattern CND-20260610-002 --reject
```

### Projects

```bash
# Add a project
aios project add "Refactor auth layer" --type project --deadline 2026-08-01 --weight 0.8

# List / show
aios project list
aios project list --status all
aios project show PRJ-001

# Record attention (resets decay clock)
aios project touch PRJ-001 --energy high

# Update status or health
aios project update PRJ-001 --status paused
aios project update PRJ-001 --health at_risk
```

**Project statuses:** `draft` → `active` → `paused` | `at_risk` | `stalled` → `completed` | `cancelled` | `abandoned`

**Attention states:** `active` → `dormant` (7 days) → `forgotten` (21 days); `resurfaced` on touch

### Commitments

```bash
# Add a commitment
aios commit add "Submit Q3 roadmap" --deadline 2026-07-15 --weight 0.9
aios commit add "Code review for PR #42" --deadline 2026-06-12 --project PRJ-001

# List / fulfill
aios commit list
aios commit list --status all
aios commit fulfill CMT-001
```

### Persona

```bash
# Initialise (once)
aios persona init --name "Erik"

# Show full persona
aios persona show

# Declare values (lower priority number = higher importance)
aios persona set-value "Deep work" --priority 1 --category professional
aios persona set-value "Family time" --priority 2 --category personal

# Declare facts
aios persona add-fact "I do my best thinking in the morning" --category habit --confidence high
aios persona add-fact "I prefer async over synchronous meetings" --category preference
```

---

## Store Layout

All data lives under `platform/knowledge/`:

```
platform/knowledge/
├── daemon/
│   └── state.yaml              # daemon cycle state
├── observations/
│   └── YYYY/MM/YYYY-MM-DD.yaml # daily observation files
├── patterns/
│   └── YYYY/MM/YYYY-MM-DD.yaml # pattern candidates
├── projects/
│   └── PRJ-NNN.yaml            # one file per project
├── commitments/
│   └── CMT-NNN.yaml            # one file per commitment
└── persona/
    └── persona.yaml            # single operator persona (PRS-001)
```

All writes are atomic (temp-file rename). All files are human-readable YAML and safe to inspect or version-control.

---

## Key Files

| File | Purpose |
|------|---------|
| `src/daemon.py` | Event loop, process lifecycle, daemonization |
| `src/daemon_state.py` | State persistence, path resolution |
| `src/cli.py` | CLI dispatcher for all `aios` commands |
| `src/project_store.py` | ProjectStore, CommitmentStore, PersonaStore |
| `src/stores.py` | PatternStore, ContradictionStore, PredictionStore |
| `src/attention_manager.py` | Attention decay engine, TrackedItem |
| `src/rules_engine.py` | Deterministic priority scoring, stall/deadline detection |
| `src/learning_engine.py` | Five-stage inference pipeline, confidence scoring |
| `src/pattern_detector.py` | Seven behavioural pattern detectors |
| `src/capture/git_capture.py` | Git activity capture source |
| `schema/` | YAML schemas for projects, commitments, persona |

---

## Configuration

| Environment variable | Default | Purpose |
|---------------------|---------|---------|
| `AIOS_CYCLE_SECONDS` | `300` | Seconds between daemon cycles |
| `AIOS_LOG_LEVEL` | `INFO` | Logging level |

---

## Related ADRs

- ADR-007: Identity as Domain Object
- ADR-008: Observation Store Architecture
- ADR-009: Executive Reasoning Engine Pattern (two-layer)
- ADR-010: Runtime Model Evolution (two-runtime coexistence)
- ADR-011: Learning Architecture
