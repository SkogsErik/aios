"""
test_daemon.py — Tests for ExecutiveDaemon lifecycle, daemonization, and values loading.
"""

import datetime
import os
import signal
import threading
import time
from pathlib import Path

import pytest
import yaml

from daemon import ExecutiveDaemon
from daemon_state import DaemonState, PidFile, RuntimeConfig, StateManager
from learning_engine import DeclaredValue, Observation


@pytest.fixture()
def tmp_base(tmp_path):
    return tmp_path / "knowledge"


@pytest.fixture()
def daemon(tmp_base):
    mgr = StateManager(base_dir=tmp_base)
    mgr.ensure_dirs()
    daemon = ExecutiveDaemon(state_mgr=mgr)
    return daemon


# -------------------------------------------------------------------
# Declared values loading
# -------------------------------------------------------------------


class TestLoadDeclaredValues:
    def test_no_values_file_returns_empty(self, daemon):
        values = daemon._load_declared_values()
        assert values == []

    def test_loads_values_from_yaml(self, daemon, tmp_base):
        values_dir = tmp_base / "persona"
        values_dir.mkdir(parents=True)
        with open(values_dir / "values.yaml", "w") as f:
            yaml.dump(
                {
                    "values": [
                        {"attribute": "deep_work_weight", "value": 0.8, "weight": 0.9},
                    ]
                },
                f,
            )
        values = daemon._load_declared_values()
        assert len(values) == 1
        assert values[0].attribute == "deep_work_weight"
        assert values[0].value == 0.8
        assert values[0].weight == 0.9

    def test_uses_default_weight_when_missing(self, daemon, tmp_base):
        values_dir = tmp_base / "persona"
        values_dir.mkdir(parents=True)
        with open(values_dir / "values.yaml", "w") as f:
            yaml.dump(
                {
                    "values": [
                        {"attribute": "test_attr", "value": 0.5},
                    ]
                },
                f,
            )
        values = daemon._load_declared_values()
        assert values[0].weight == 0.5

    def test_handles_empty_values(self, daemon, tmp_base):
        values_dir = tmp_base / "persona"
        values_dir.mkdir(parents=True)
        with open(values_dir / "values.yaml", "w") as f:
            yaml.dump({"values": []}, f)
        assert daemon._load_declared_values() == []


# -------------------------------------------------------------------
# Observation persistence
# -------------------------------------------------------------------


class TestObservationPersistence:
    def test_save_and_load_recent(self, daemon, tmp_base):
        obs = Observation(
            id="OBS-TEST-001",
            timestamp=datetime.datetime.now(),
            type="note",
            source_mechanism="manual",
            source_component="test",
            summary="test observation",
            project="PRJ-001",
            energy="high",
            tags=["test"],
        )
        daemon._save_observation(obs)
        loaded = daemon._load_recent_observations()
        assert len(loaded) == 1
        assert loaded[0].id == "OBS-TEST-001"
        assert loaded[0].summary == "test observation"

    def test_load_respects_cutoff(self, daemon, tmp_base):
        old_obs = Observation(
            id="OBS-OLD-001",
            timestamp=datetime.datetime.now() - datetime.timedelta(days=100),
            type="note",
            source_mechanism="manual",
            source_component="test",
            summary="old observation",
            project="PRJ-000",
            energy=None,
            tags=[],
        )
        daemon._save_observation(old_obs)
        loaded = daemon._load_recent_observations()
        assert len(loaded) == 0


# -------------------------------------------------------------------
# Daemon lifecycle (non-daemonized)
# -------------------------------------------------------------------


class TestDaemonLifecycle:
    def test_start_stop_without_daemonize(self, tmp_base):
        mgr = StateManager(base_dir=tmp_base)
        mgr.ensure_dirs()
        pid_file = PidFile(path=tmp_base / "test-daemon.pid")
        daemon = ExecutiveDaemon(state_mgr=mgr, pid_file=pid_file)
        config = daemon._config._replace(cycle_seconds=1, schedule_n=99, daemonize=False)
        daemon._config = config

        def stop_after_delay():
            time.sleep(0.05)
            daemon.stop()

        t = threading.Thread(target=stop_after_delay, daemon=True)
        t.start()
        daemon.start()
        t.join()
        assert daemon._running is False
        assert daemon._cycle_count >= 0

    def test_start_rejects_when_already_running(self, tmp_base):
        mgr = StateManager(base_dir=tmp_base)
        mgr.ensure_dirs()
        pid_file = PidFile(path=tmp_base / "already.pid")
        pid_file.write(999999)
        daemon = ExecutiveDaemon(state_mgr=mgr, pid_file=pid_file)
        daemon.start()
        assert daemon._running is False

    def test_stop_removes_pid(self, tmp_base):
        pid_file = PidFile(path=tmp_base / "cleanup.pid")
        pid_file.write(12345)
        mgr = StateManager(base_dir=tmp_base)
        daemon = ExecutiveDaemon(state_mgr=mgr, pid_file=pid_file)
        daemon._running = True
        daemon.stop()
        assert daemon._running is False
        assert pid_file.read() is None

    def test_save_checkpoint_persists_state(self, daemon, tmp_base):
        daemon._cycle_count = 42
        daemon._obs_counter = 100
        daemon._state = daemon._state._replace(pattern_counter=7)
        daemon._save_checkpoint()
        loaded = daemon._state_mgr.load_state()
        assert loaded.cycle_count == 42
        assert loaded.observation_counter == 100
        assert loaded.pattern_counter == 7

    def test_graph_cycle(self, daemon, tmp_base):
        daemon._cycle_count = 3
        daemon._obs_counter = 5
        cfg = daemon._config._replace(cycle_seconds=1, schedule_n=2, daemonize=False)
        daemon._config = cfg

        def stop_soon():
            time.sleep(0.05)
            daemon.stop()

        t = threading.Thread(target=stop_soon, daemon=True)
        t.start()
        daemon.start()
        t.join()


# -------------------------------------------------------------------
# Daemonization (stdio redirect)
# -------------------------------------------------------------------


class TestDaemonization:
    def test_redirect_stdio_creates_log_file(self, tmp_base):
        mgr = StateManager(base_dir=tmp_base)
        mgr.ensure_dirs()
        daemon = ExecutiveDaemon(state_mgr=mgr)
        daemon._redirect_stdio()
        log_path = tmp_base / "daemon" / "daemon.log"
        assert log_path.exists()
        assert log_path.stat().st_size >= 0


# -------------------------------------------------------------------
# Event loop components
# -------------------------------------------------------------------


class TestPatternDetection:
    def test_skip_when_few_observations(self, daemon):
        daemon._run_pattern_detection([])
        pass

    def test_skip_when_insufficient_windows(self, daemon, tmp_base):
        today = datetime.date.today()
        obs = Observation(
            id="OBS-T-001",
            timestamp=datetime.datetime.now(),
            type="note",
            source_mechanism="manual",
            source_component="test",
            summary="single obs",
            project="PRJ-000",
            energy="medium",
            tags=[],
        )
        daemon._save_observation(obs)
        items = daemon._load_tracked_items()
        daemon._run_pattern_detection(items)
        pass
