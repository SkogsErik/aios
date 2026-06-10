"""
daemon_state.py — State persistence and configuration for the executive daemon.

Manages:
  - Daemon runtime state (last run, cycle count, last git hashes)
  - Configuration loading (git repos, timing parameters)
  - Store path resolution
"""

import datetime
import os
import shutil
import tempfile
from pathlib import Path
from typing import NamedTuple

import yaml


DEFAULT_BASE_DIR = Path("platform/knowledge")
STATE_FILE = DEFAULT_BASE_DIR / "daemon" / "state.yaml"


class DaemonState(NamedTuple):
    last_run: str
    cycle_count: int
    last_git_hashes: dict[str, str]
    observation_counter: int
    pattern_counter: int


class RuntimeConfig(NamedTuple):
    cycle_seconds: int
    schedule_n: int
    git_poll_depth: int
    daemonize: bool


def default_config() -> RuntimeConfig:
    return RuntimeConfig(
        cycle_seconds=int(os.environ.get("AIOS_CYCLE_SECONDS", "300")),
        schedule_n=int(os.environ.get("AIOS_SCHEDULE_N", "12")),
        git_poll_depth=int(os.environ.get("AIOS_GIT_POLL_DEPTH", "50")),
        daemonize=os.environ.get("AIOS_DAEMONIZE", "1") == "1",
    )


class StateManager:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or DEFAULT_BASE_DIR
        self._state_path = self._base / "daemon" / "state.yaml"

    def ensure_dirs(self) -> None:
        (self._base / "daemon").mkdir(parents=True, exist_ok=True)
        (self._base / "observations").mkdir(parents=True, exist_ok=True)
        (self._base / "patterns").mkdir(parents=True, exist_ok=True)
        (self._base / "contradictions").mkdir(parents=True, exist_ok=True)
        (self._base / "predictions").mkdir(parents=True, exist_ok=True)

    def load_state(self) -> DaemonState:
        if not self._state_path.exists():
            return DaemonState(
                last_run="",
                cycle_count=0,
                last_git_hashes={},
                observation_counter=0,
                pattern_counter=0,
            )
        with open(self._state_path) as f:
            data = yaml.safe_load(f) or {}
        return DaemonState(
            last_run=data.get("last_run", ""),
            cycle_count=data.get("cycle_count", 0),
            last_git_hashes=data.get("last_git_hashes", {}),
            observation_counter=data.get("observation_counter", 0),
            pattern_counter=data.get("pattern_counter", 0),
        )

    def save_state(self, state: DaemonState) -> None:
        self.ensure_dirs()
        data = {
            "last_run": state.last_run,
            "cycle_count": state.cycle_count,
            "last_git_hashes": state.last_git_hashes,
            "observation_counter": state.observation_counter,
            "pattern_counter": state.pattern_counter,
        }
        atomic_path = self._state_path.with_suffix(".yaml.tmp")
        with open(atomic_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        shutil.move(str(atomic_path), str(self._state_path))

    def load_config(self) -> RuntimeConfig:
        return default_config()

    @property
    def state_path(self) -> Path:
        return self._state_path


class PidFile:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("/tmp/aios-daemon.pid")

    def write(self, pid: int) -> None:
        self._path.write_text(str(pid))

    def read(self) -> int | None:
        if not self._path.exists():
            return None
        try:
            return int(self._path.read_text().strip())
        except (ValueError, OSError):
            return None

    def remove(self) -> None:
        if self._path.exists():
            self._path.unlink()

    def is_running(self) -> bool:
        pid = self.read()
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            self.remove()
            return False

    @property
    def path(self) -> Path:
        return self._path
