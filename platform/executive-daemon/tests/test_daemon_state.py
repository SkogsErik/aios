"""
test_daemon_state.py — Tests for state persistence and config loading.
"""

import datetime
import os
from pathlib import Path

import pytest
import yaml

from daemon_state import DaemonState, PidFile, StateManager


@pytest.fixture()
def tmp_base(tmp_path):
    return tmp_path / "knowledge"


class TestStateManager:
    def test_load_empty_state(self, tmp_base):
        mgr = StateManager(base_dir=tmp_base)
        state = mgr.load_state()
        assert state.cycle_count == 0
        assert state.observation_counter == 0
        assert state.last_git_hashes == {}

    def test_save_and_load(self, tmp_base):
        mgr = StateManager(base_dir=tmp_base)
        state = DaemonState(
            last_run="2026-06-10T14:00:00",
            cycle_count=42,
            last_git_hashes={"/repo": "abc123"},
            observation_counter=100,
            pattern_counter=5,
        )
        mgr.save_state(state)
        loaded = mgr.load_state()
        assert loaded.cycle_count == 42
        assert loaded.observation_counter == 100
        assert loaded.last_git_hashes["/repo"] == "abc123"

    def test_ensure_dirs_creates_directories(self, tmp_base):
        mgr = StateManager(base_dir=tmp_base)
        mgr.ensure_dirs()
        assert (tmp_base / "daemon").exists()
        assert (tmp_base / "observations").exists()
        assert (tmp_base / "patterns").exists()
        assert (tmp_base / "contradictions").exists()


class TestPidFile:
    def test_write_and_read(self, tmp_path):
        pid_file = PidFile(path=tmp_path / "test.pid")
        pid_file.write(1234)
        assert pid_file.read() == 1234

    def test_read_nonexistent(self, tmp_path):
        pid_file = PidFile(path=tmp_path / "nonexistent.pid")
        assert pid_file.read() is None

    def test_is_running_false_for_stale(self, tmp_path):
        pid_file = PidFile(path=tmp_path / "stale.pid")
        pid_file.write(99999999)
        assert pid_file.is_running() is False

    def test_remove(self, tmp_path):
        pid_file = PidFile(path=tmp_path / "remove.pid")
        pid_file.write(123)
        pid_file.remove()
        assert not pid_file.path.exists()
