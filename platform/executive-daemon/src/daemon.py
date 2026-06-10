"""
daemon.py — Executive daemon event loop and process lifecycle.

Runs the continuous cycle: capture → store → attention → rules → pattern detection.
Manages background daemonization via PID file.
"""

import datetime
import logging
import os
import signal
import sys
import time
from pathlib import Path

import yaml

from attention_manager import (
    AttentionManager,
    AttentionState,
    TrackedItem,
)
from capture.git_capture import (
    GitRepoConfig,
    GitCaptureResult,
    git_poll,
    load_git_config,
)
from daemon_state import DaemonState, PidFile, RuntimeConfig, StateManager
from learning_engine import (
    AggregatedWindow,
    ConfidenceScorer,
    DeclaredValue,
    LearningEngine,
    Observation,
    PatternCandidate,
    PatternStatus,
    PreferenceReconciler,
    Tension,
)
from pattern_detector import (
    BehavioralBiasDetector,
    ProjectPriorityPair,
)
from rules_engine import (
    Commitment,
    DeadlineScorer,
    FragmentationDetector,
    RulesEngine,
    StallDetector,
    TrackedItem as RETrackedItem,
    PriorityResult,
)
from stores import (
    ContradictionStore,
    PatternStore,
    PredictionStore,
)

logger = logging.getLogger("aios.daemon")


class ExecutiveDaemon:
    def __init__(
        self,
        state_mgr: StateManager | None = None,
        pid_file: PidFile | None = None,
    ) -> None:
        self._state_mgr = state_mgr or StateManager()
        self._pid_file = pid_file or PidFile()
        self._config = self._state_mgr.load_config()
        self._running = False

        # Components
        self._attention_mgr = AttentionManager()
        self._rules_engine = RulesEngine()
        self._learning_engine = LearningEngine()
        self._stall_detector = StallDetector(stall_threshold_days=14)
        self._behavioral_bias = BehavioralBiasDetector()
        self._pattern_store = PatternStore()
        self._contradiction_store = ContradictionStore()

        # Runtime state
        self._state = self._state_mgr.load_state()
        self._cycle_count = self._state.cycle_count
        self._obs_counter = self._state.observation_counter

    # -------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------

    def start(self) -> None:
        if self._pid_file.is_running():
            print("Daemon is already running (PID {})".format(self._pid_file.read()))
            return
        self._state_mgr.ensure_dirs()
        if self._config.daemonize:
            self._daemonize()
        self._running = True
        self._pid_file.write(os.getpid())
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        logger.info("Daemon started (PID %d, cycle=%ds)", os.getpid(), self._config.cycle_seconds)
        self._event_loop()

    def stop(self) -> None:
        logger.info("Daemon stopping")
        self._running = False
        self._pid_file.remove()

    # -------------------------------------------------------------------
    # Daemonization
    # -------------------------------------------------------------------

    def _daemonize(self) -> None:
        pid = os.fork()
        if pid > 0:
            print("Daemon started")
            sys.stdout.flush()
            os._exit(0)
        os.setsid()
        os.umask(0)
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        self._redirect_stdio()

    def _redirect_stdio(self) -> None:
        log_path = self._state_mgr._base / "daemon" / "daemon.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout.flush()
        sys.stderr.flush()
        devnull_fd = os.open(os.devnull, os.O_RDONLY)
        log_fd = os.open(str(log_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        os.dup2(devnull_fd, 0)
        os.dup2(log_fd, 1)
        os.dup2(log_fd, 2)
        for fd in (devnull_fd, log_fd):
            if fd > 2:
                os.close(fd)

    def _handle_signal(self, signum, frame) -> None:
        logger.info("Received signal %d", signum)
        self.stop()

    # -------------------------------------------------------------------
    # Event loop
    # -------------------------------------------------------------------

    def _event_loop(self) -> None:
        cycle_count = 0
        while self._running:
            try:
                self._run_cycle(cycle_count)
                cycle_count += 1
                self._cycle_count = cycle_count
                self._save_checkpoint()
            except Exception as e:
                logger.error("Cycle %d failed: %s", cycle_count, e, exc_info=True)
            for _ in range(self._config.cycle_seconds):
                if not self._running:
                    break
                time.sleep(1)

    def _run_cycle(self, cycle_num: int) -> None:
        # 1. Git capture
        git_configs = load_git_config(self._state_mgr._base)
        for gc in git_configs:
            last_hash = self._state.last_git_hashes.get(gc.path)
            result = git_poll(gc, last_hash, self._obs_counter)
            for obs in result.observations:
                self._obs_counter += 1
                self._save_observation(obs)
            if result.last_commit and result.last_commit != last_hash:
                self._state = self._state._replace(
                    last_git_hashes={**self._state.last_git_hashes, gc.path: result.last_commit}
                )

        # 2. Attention decay
        stored_items = self._load_tracked_items()
        if stored_items:
            today = datetime.date.today()
            transitions = self._attention_mgr.evaluate_all(stored_items, today)
            for item, new_state in transitions:
                logger.debug("Attention: %s -> %s", item.id, new_state)

        # 3. Stall detection
        stalled = self._rules_engine.check_stalls(stored_items, datetime.date.today())
        for s in stalled:
            logger.info("STALL: %s (last touch: %s)", s.id, s.last_touch)

        # 4. Priority scoring
        commitments = self._load_commitments()
        priorities = self._rules_engine.compute_priorities(
            stored_items, commitments, datetime.date.today()
        )

        # 5. Pattern detection (every SCHEDULE_N cycles)
        if cycle_num > 0 and cycle_num % self._config.schedule_n == 0:
            self._run_pattern_detection(stored_items)

    # -------------------------------------------------------------------
    # Pattern detection
    # -------------------------------------------------------------------

    def _run_pattern_detection(self, items: list[RETrackedItem]) -> None:
        recent_obs = self._load_recent_observations()
        if len(recent_obs) < 5:
            logger.debug("Pattern detection skipped: only %d observations", len(recent_obs))
            return
        windows = self._build_windows(recent_obs)
        if len(windows) < 3:
            logger.debug("Pattern detection skipped: only %d windows", len(windows))
            return

        pattern_counter = self._state.pattern_counter

        # Preference reconciliation (requires declared values)
        declared = self._load_declared_values()
        if declared and windows:
            aggregated = windows[-1]
            tensions = self._learning_engine.reconcile(declared, aggregated)
            for t in tensions:
                self._contradiction_store.save(t)
            candidates, pattern_counter = self._learning_engine.generate_candidates(
                tensions, windows, {}, pattern_counter
            )
            for c in candidates:
                self._pattern_store.save(c)
                logger.info("PATTERN: %s (confidence=%.2f)", c.title, c.confidence)

        # Behavioral bias (works without declared values)
        if len(windows) >= 3:
            pairs = [ProjectPriorityPair("default_a", "default_b", 0.5, 0.5)]
            bias_results = self._behavioral_bias.detect(windows, pairs, pattern_counter)
            for c in bias_results:
                self._pattern_store.save(c)
                pattern_counter += 1
                logger.info("PATTERN: %s (confidence=%.2f)", c.title, c.confidence)

        self._state = self._state._replace(pattern_counter=pattern_counter)

    # -------------------------------------------------------------------
    # Persistence helpers
    # -------------------------------------------------------------------

    def _save_observation(self, obs: Observation) -> None:
        date_str = obs.timestamp.strftime("%Y-%m-%d")
        obs_dir = self._state_mgr._base / "observations" / obs.timestamp.strftime("%Y/%m")
        obs_dir.mkdir(parents=True, exist_ok=True)
        obs_file = obs_dir / f"{date_str}.yaml"
        entry = {
            "id": obs.id,
            "timestamp": obs.timestamp.isoformat(),
            "type": obs.type,
            "source_mechanism": obs.source_mechanism,
            "source_component": obs.source_component,
            "summary": obs.summary,
            "project": obs.project,
            "energy": obs.energy,
            "tags": obs.tags,
        }
        records: list[dict] = []
        if obs_file.exists():
            with open(obs_file) as f:
                records = yaml.safe_load(f) or []
        records.append(entry)
        with open(obs_file, "w") as f:
            yaml.dump(records, f, default_flow_style=False, sort_keys=False)

    def _load_tracked_items(self) -> list[RETrackedItem]:
        from project_store import ProjectStore
        store = ProjectStore(self._state_mgr._base / "projects")
        return store.list_as_tracked_items()

    def _load_commitments(self) -> list[Commitment]:
        from project_store import CommitmentStore
        store = CommitmentStore(self._state_mgr._base / "commitments")
        return store.list_as_rules_engine_commitments()

    def _load_declared_values(self) -> list[DeclaredValue]:
        values_path = self._state_mgr._base / "persona" / "values.yaml"
        if not values_path.exists():
            return []
        with open(values_path) as f:
            data = yaml.safe_load(f) or {}
        result: list[DeclaredValue] = []
        for entry in data.get("values", []):
            result.append(
                DeclaredValue(
                    attribute=entry["attribute"],
                    value=entry["value"],
                    weight=entry.get("weight", 0.5),
                )
            )
        return result

    def _load_recent_observations(self) -> list[Observation]:
        results: list[Observation] = []
        base = self._state_mgr._base / "observations"
        if not base.exists():
            return results
        cutoff = datetime.date.today() - datetime.timedelta(days=90)
        for root, _dirs, files in os.walk(base):
            for fn in sorted(files, reverse=True):
                if not fn.endswith(".yaml"):
                    continue
                try:
                    d = datetime.date.fromisoformat(fn.replace(".yaml", ""))
                except ValueError:
                    continue
                if d < cutoff:
                    continue
                with open(Path(root) / fn) as f:
                    records = yaml.safe_load(f) or []
                for r in records:
                    results.append(
                        Observation(
                            id=r.get("id", ""),
                            timestamp=datetime.datetime.fromisoformat(r.get("timestamp", "")),
                            type=r.get("type", "action"),
                            source_mechanism=r.get("source_mechanism", "auto"),
                            source_component=r.get("source_component", "unknown"),
                            summary=r.get("summary", ""),
                            project=r.get("project"),
                            energy=r.get("energy"),
                            tags=r.get("tags", []),
                        )
                    )
        return results

    def _build_windows(self, observations: list[Observation]) -> list[AggregatedWindow]:
        if not observations:
            return []
        by_week: dict[tuple[int, int], list[Observation]] = {}
        for obs in observations:
            iso = obs.timestamp.isocalendar()
            key = (iso[0], iso[1])
            if key not in by_week:
                by_week[key] = []
            by_week[key].append(obs)
        windows: list[AggregatedWindow] = []
        for (year, week), obs_list in sorted(by_week.items()):
            first_day = datetime.date.fromisocalendar(year, week, 1)
            last_day = datetime.date.fromisocalendar(year, week, 7)
            windows.append(
                self._learning_engine.run_aggregation(obs_list, first_day, last_day)
            )
        return windows

    def _save_checkpoint(self) -> None:
        now_str = datetime.datetime.now().isoformat()
        state = DaemonState(
            last_run=now_str,
            cycle_count=self._cycle_count,
            last_git_hashes=self._state.last_git_hashes,
            observation_counter=self._obs_counter,
            pattern_counter=self._state.pattern_counter,
        )
        self._state_mgr.save_state(state)
