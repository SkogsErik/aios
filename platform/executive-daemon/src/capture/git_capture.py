"""
git_capture.py — Git observation capture via polling.

Polls configured git repositories for new commits and generates
observations following ADR-008 schema. The last-seen commit hash
is tracked in daemon state to avoid duplicate observations.
"""

import datetime
import logging
import subprocess
import uuid
from pathlib import Path
from typing import NamedTuple

from learning_engine import Observation

logger = logging.getLogger(__name__)


class GitRepoConfig(NamedTuple):
    path: str
    default_project: str | None
    tag_prefix: str


class GitCaptureResult(NamedTuple):
    observations: list[Observation]
    last_commit: str | None


def _run_git_log(repo_path: str, after_hash: str | None, max_count: int = 50) -> list[dict]:
    cmd = ["git", "log", f"--max-count={max_count}", "--format=%H|%ai|%s"]
    if after_hash:
        cmd.append(f"{after_hash}..HEAD")
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("git log failed for %s: %s", repo_path, e)
        return []
    if result.returncode != 0:
        logger.warning("git log error in %s: %s", repo_path, result.stderr.strip())
        return []
    entries: list[dict] = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            entries.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return entries


def _parse_timestamp(iso_str: str) -> datetime.datetime:
    try:
        return datetime.datetime.fromisoformat(iso_str)
    except ValueError:
        return datetime.datetime.now()


def _compute_observation_id(date_str: str, counter: int) -> str:
    date_part = date_str.replace("-", "")
    return f"OBS-{date_part}-{counter:03d}"


def git_poll(
    config: GitRepoConfig,
    last_known_hash: str | None,
    observation_counter: int,
) -> GitCaptureResult:
    entries = _run_git_log(config.path, last_known_hash)
    if not entries:
        return GitCaptureResult(observations=[], last_commit=last_known_hash)
    observations: list[Observation] = []
    for entry in reversed(entries):
        ts = _parse_timestamp(entry["date"])
        summary = entry["subject"]
        observation_counter += 1
        obs = Observation(
            id=_compute_observation_id(ts.strftime("%Y%m%d"), observation_counter),
            timestamp=ts,
            type="action",
            source_mechanism="auto",
            source_component="git",
            summary=summary,
            project=config.default_project,
            energy=None,
            tags=["git", "commit"],
        )
        observations.append(obs)
    last_commit = entries[0]["hash"]
    logger.info(
        "git_poll: %d new commits in %s (last: %s)",
        len(observations),
        config.path,
        last_commit[:12],
    )
    return GitCaptureResult(observations=observations, last_commit=last_commit)


def load_git_config(base_dir: Path) -> list[GitRepoConfig]:
    import yaml
    config_path = base_dir / "daemon" / "config.yaml"
    if not config_path.exists():
        return []
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    repos = data.get("git", {}).get("repos", {})
    configs: list[GitRepoConfig] = []
    for repo_path, cfg in repos.items():
        configs.append(
            GitRepoConfig(
                path=repo_path,
                default_project=cfg.get("project"),
                tag_prefix=cfg.get("tag_prefix", ""),
            )
        )
    return configs
