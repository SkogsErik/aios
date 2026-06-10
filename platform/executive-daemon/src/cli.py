"""
cli.py — CLI dispatcher for the AIOS executive daemon.

Commands:
  aios start            Start daemon in background
  aios stop             Stop daemon
  aios status           Show daemon status
  aios observe <msg>    Capture a manual observation
  aios patterns         List recent pattern candidates
  aios pattern <id>     Show / accept / reject a pattern
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
from pathlib import Path

from daemon import ExecutiveDaemon
from daemon_state import PidFile, StateManager


def _get_state_mgr() -> StateManager:
    base = Path("platform/knowledge")
    return StateManager(base_dir=base)


def _get_pid_file() -> PidFile:
    return PidFile()


def _print_error(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_start(args: argparse.Namespace) -> None:
    pid_file = _get_pid_file()
    if pid_file.is_running():
        print(f"Daemon already running (PID {pid_file.read()})")
        return
    daemon = ExecutiveDaemon(state_mgr=_get_state_mgr(), pid_file=pid_file)
    daemon.start()


def cmd_stop(args: argparse.Namespace) -> None:
    pid_file = _get_pid_file()
    pid = pid_file.read()
    if pid is None:
        print("Daemon not running")
        return
    try:
        os.kill(pid, 15)  # SIGTERM
        print(f"Sent stop signal to PID {pid}")
    except ProcessLookupError:
        print("Daemon not running (stale PID file)")
        pid_file.remove()


def cmd_status(args: argparse.Namespace) -> None:
    pid_file = _get_pid_file()
    pid = pid_file.read()
    if pid is None or not pid_file.is_running():
        print("Daemon: stopped")
        return
    state_mgr = _get_state_mgr()
    state = state_mgr.load_state()
    print(f"Daemon: running (PID {pid})")
    print(f"  Cycles completed:   {state.cycle_count}")
    print(f"  Last run:           {state.last_run or 'never'}")
    print(f"  Observation count:  {state.observation_counter}")
    print(f"  Pattern count:      {state.pattern_counter}")
    print(f"  Watched repos:      {len(state.last_git_hashes)}")
    for repo, last_hash in state.last_git_hashes.items():
        print(f"    {repo}: {last_hash[:12]}" if last_hash else f"    {repo}: (no commits yet)")


def cmd_observe(args: argparse.Namespace) -> None:
    from learning_engine import Observation
    text = " ".join(args.text)
    obs = Observation(
        id=f"OBS-{datetime.date.today().isoformat().replace('-', '')}-MAN",
        timestamp=datetime.datetime.now(),
        type="note",
        source_mechanism="manual",
        source_component="cli",
        summary=text,
        project=args.project,
        energy=args.energy,
        tags=args.tags.split(",") if args.tags else ["manual"],
    )
    state_mgr = _get_state_mgr()
    daemon = ExecutiveDaemon(state_mgr=state_mgr)
    daemon._save_observation(obs)
    print(f"Observation recorded: {obs.id}")


def cmd_patterns(args: argparse.Namespace) -> None:
    from stores import PatternStore
    store = PatternStore()
    recent = store.list_recent(days=args.days)
    if not recent:
        print("No patterns found.")
        return
    for p in recent:
        status = p.get("status", "unknown")
        print(f"  {p['id']:20s} [{p.get('pattern_type', '?'):25s}] conf={p.get('confidence', 0):.2f}  {p.get('title', '')[:60]}")


def cmd_pattern_detail(args: argparse.Namespace) -> None:
    from stores import PatternStore
    store = PatternStore()
    recent = store.list_recent(days=365)
    found = [p for p in recent if p.get("id") == args.pattern_id]
    if not found:
        _print_error(f"Pattern '{args.pattern_id}' not found")
        return
    p = found[0]
    print(f"ID:          {p['id']}")
    print(f"Type:        {p.get('pattern_type', '?')}")
    print(f"Confidence:  {p.get('confidence', 0):.2f}")
    print(f"Status:      {p.get('status', '?')}")
    print(f"Title:       {p.get('title', '')}")
    print(f"Description: {p.get('description', '')}")
    if p.get("suggestions"):
        print("Suggestions:")
        for s in p["suggestions"]:
            print(f"  - {s}")
    if args.accept:
        from learning_engine import PatternStatus
        print("Pattern accepted (logic pending operator review interface)")
    elif args.reject:
        print("Pattern rejected (confidence will decay)")


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aios", description="AIOS Executive Daemon")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="Start the executive daemon")
    start.set_defaults(func=cmd_start)

    stop = sub.add_parser("stop", help="Stop the executive daemon")
    stop.set_defaults(func=cmd_stop)

    status = sub.add_parser("status", help="Show daemon status")
    status.set_defaults(func=cmd_status)

    observe = sub.add_parser("observe", help="Record a manual observation")
    observe.add_argument("text", nargs="+", help="Observation text")
    observe.add_argument("--project", default=None, help="Project ID (PRJ-xxx)")
    observe.add_argument("--energy", choices=["high", "medium", "low"], default=None)
    observe.add_argument("--tags", default="", help="Comma-separated tags")
    observe.set_defaults(func=cmd_observe)

    patterns = sub.add_parser("patterns", help="List pattern candidates")
    patterns.add_argument("--days", type=int, default=7, help="Lookback window")
    patterns.set_defaults(func=cmd_patterns)

    pattern = sub.add_parser("pattern", help="Show/act on a pattern")
    pattern.add_argument("pattern_id", help="Pattern ID (CND-xxxx)")
    pattern.add_argument("--accept", action="store_true", help="Accept pattern")
    pattern.add_argument("--reject", action="store_true", help="Reject pattern")
    pattern.add_argument("--dismiss", action="store_true", help="Dismiss pattern")
    pattern.set_defaults(func=cmd_pattern_detail)

    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
