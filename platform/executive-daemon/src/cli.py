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


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_KNOWLEDGE_DIR = _REPO_ROOT / "platform" / "knowledge"


def _get_state_mgr() -> StateManager:
    return StateManager(base_dir=_KNOWLEDGE_DIR)


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
    state_mgr = _get_state_mgr()
    state = state_mgr.load_state()
    counter = state.observation_counter + 1
    date_str = datetime.date.today().strftime("%Y%m%d")
    obs = Observation(
        id=f"OBS-{date_str}-{counter:03d}",
        timestamp=datetime.datetime.now(),
        type="note",
        source_mechanism="manual",
        source_component="cli",
        summary=text,
        project=args.project,
        energy=args.energy,
        tags=args.tags.split(",") if args.tags else ["manual"],
    )
    new_state = state._replace(observation_counter=counter)
    state_mgr.save_state(new_state)
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
# Project commands
# ---------------------------------------------------------------------------


def cmd_project_add(args: argparse.Namespace) -> None:
    from project_store import Project, ProjectStore
    store = ProjectStore()
    project_id = store.next_id()
    today = datetime.date.today()
    target = None
    if args.deadline:
        try:
            target = datetime.date.fromisoformat(args.deadline)
        except ValueError:
            _print_error(f"Invalid deadline format '{args.deadline}' — use YYYY-MM-DD")
            return
    project = Project(
        id=project_id,
        title=args.title,
        type=args.type,
        status="active",
        created=today,
        updated=today,
        goal=args.goal,
        description=args.description,
        target_completion=target,
        priority_weight=args.weight,
        attention_state="active",
        last_touch=today,
    )
    store.save(project)
    print(f"Project created: {project_id}  {args.title}")


def cmd_project_list(args: argparse.Namespace) -> None:
    from project_store import ProjectStore
    store = ProjectStore()
    projects = store.list_all() if args.status == "all" else store.list_active()
    if not projects:
        print("No projects found.")
        return
    print(f"{'ID':<10} {'STATUS':<12} {'HEALTH':<10} {'ATTENTION':<12} {'TITLE'}")
    print("-" * 72)
    for p in projects:
        print(f"{p.id:<10} {p.status:<12} {p.health:<10} {p.attention_state:<12} {p.title}")


def cmd_project_show(args: argparse.Namespace) -> None:
    from project_store import ProjectStore
    store = ProjectStore()
    p = store.get(args.project_id)
    if p is None:
        _print_error(f"Project '{args.project_id}' not found")
        return
    print(f"ID:              {p.id}")
    print(f"Title:           {p.title}")
    print(f"Type:            {p.type}")
    print(f"Status:          {p.status}")
    print(f"Health:          {p.health}")
    print(f"Priority weight: {p.priority_weight:.2f}")
    print(f"Attention:       {p.attention_state}")
    print(f"Last touch:      {p.last_touch or p.created}")
    if p.target_completion:
        today = datetime.date.today()
        days_left = (p.target_completion - today).days
        flag = " ⚠️ " if days_left < 7 else ""
        print(f"Target date:     {p.target_completion}{flag} ({days_left} days)")
    if p.goal:
        print(f"Goal:            {p.goal}")
    if p.description:
        print(f"Description:     {p.description}")
    if p.commitments:
        print(f"Commitments:     {', '.join(p.commitments)}")
    if p.tags:
        print(f"Tags:            {', '.join(p.tags)}")


def cmd_project_touch(args: argparse.Namespace) -> None:
    from project_store import ProjectStore
    from learning_engine import Observation
    store = ProjectStore()
    updated = store.touch(args.project_id)
    if updated is None:
        _print_error(f"Project '{args.project_id}' not found")
        return
    # Record an observation if energy is provided
    if args.energy:
        state_mgr = _get_state_mgr()
        state = state_mgr.load_state()
        counter = state.observation_counter + 1
        date_str = datetime.date.today().strftime("%Y%m%d")
        obs = Observation(
            id=f"OBS-{date_str}-{counter:03d}",
            timestamp=datetime.datetime.now(),
            type="activity",
            source_mechanism="manual",
            source_component="cli",
            summary=f"Touched {args.project_id}: {updated.title}",
            project=args.project_id,
            energy=args.energy,
            tags=["touch"],
        )
        new_state = state._replace(observation_counter=counter)
        state_mgr.save_state(new_state)
        daemon = ExecutiveDaemon(state_mgr=state_mgr)
        daemon._save_observation(obs)
    print(f"Touched {args.project_id} → attention: {updated.attention_state}")


def cmd_project_update(args: argparse.Namespace) -> None:
    from project_store import ProjectStore
    store = ProjectStore()
    if args.status:
        updated = store.update_status(args.project_id, args.status)
        if updated is None:
            _print_error(f"Project '{args.project_id}' not found")
            return
        print(f"{args.project_id} status → {updated.status}")
    if args.health:
        p = store.get(args.project_id)
        if p is None:
            _print_error(f"Project '{args.project_id}' not found")
            return
        updated = p._replace(health=args.health)
        store.save(updated)
        print(f"{args.project_id} health → {updated.health}")


# ---------------------------------------------------------------------------
# Commitment commands
# ---------------------------------------------------------------------------


def cmd_commit_add(args: argparse.Namespace) -> None:
    from project_store import CommitmentData, CommitmentStore, ProjectStore
    try:
        deadline = datetime.date.fromisoformat(args.deadline)
    except ValueError:
        _print_error(f"Invalid deadline format '{args.deadline}' — use YYYY-MM-DD")
        return
    store = CommitmentStore()
    cmt_id = store.next_id()
    today = datetime.date.today()
    commitment = CommitmentData(
        id=cmt_id,
        description=args.description,
        deadline=deadline,
        status="active",
        created=today,
        updated=today,
        project=args.project,
        promisee=args.promisee,
        weight=args.weight,
    )
    store.save(commitment)
    # Link to project if specified
    if args.project:
        proj_store = ProjectStore()
        p = proj_store.get(args.project)
        if p is not None:
            updated_cmts = list(p.commitments or []) + [cmt_id]
            proj_store.save(p._replace(commitments=updated_cmts))
    print(f"Commitment created: {cmt_id}  (deadline: {deadline}, weight: {args.weight:.1f})")


def cmd_commit_list(args: argparse.Namespace) -> None:
    from project_store import CommitmentStore
    store = CommitmentStore()
    commitments = store.list_active() if args.status == "active" else store.list_all()
    if not commitments:
        print("No commitments found.")
        return
    today = datetime.date.today()
    print(f"{'ID':<10} {'STATUS':<12} {'DEADLINE':<12} {'DAYS':<6} {'W':<5} {'DESCRIPTION'}")
    print("-" * 72)
    for c in commitments:
        days = (c.deadline - today).days
        flag = "⚠️ " if days < 3 else "   "
        print(f"{c.id:<10} {c.status:<12} {c.deadline!s:<12} {days:<6} {c.weight:<5.1f} {flag}{c.description[:40]}")


def cmd_commit_fulfill(args: argparse.Namespace) -> None:
    from project_store import CommitmentStore
    store = CommitmentStore()
    c = store.get(args.commitment_id)
    if c is None:
        _print_error(f"Commitment '{args.commitment_id}' not found")
        return
    updated = c._replace(status="fulfilled")
    store.save(updated)
    print(f"{args.commitment_id} marked as fulfilled")


# ---------------------------------------------------------------------------
# Persona commands
# ---------------------------------------------------------------------------


def cmd_persona_show(args: argparse.Namespace) -> None:
    from project_store import PersonaStore
    store = PersonaStore()
    persona = store.load()
    if persona is None:
        print("No persona defined. Run: aios persona init [--name <name>]")
        return
    print(f"Persona: {persona.id}  v{persona.version}")
    if persona.name:
        print(f"Name:    {persona.name}")
    print(f"Updated: {persona.updated}")
    if persona.values:
        print("\nValues (priority order):")
        vals = sorted(persona.values, key=lambda v: v.get("priority", 99) if isinstance(v, dict) else v.priority)
        for v in vals:
            val_str = v.get("value") if isinstance(v, dict) else v.value
            cat = v.get("category") if isinstance(v, dict) else v.category
            pri = v.get("priority") if isinstance(v, dict) else v.priority
            print(f"  [{pri}] {val_str}  ({cat})")
    if persona.declared_facts:
        print(f"\nDeclared facts: {len(persona.declared_facts)}")
        for f in persona.declared_facts:
            stmt = f.get("statement") if isinstance(f, dict) else f.statement
            cat = f.get("category") if isinstance(f, dict) else f.category
            conf = f.get("confidence") if isinstance(f, dict) else f.confidence
            print(f"  [{cat}/{conf}] {stmt}")
    if persona.preferences:
        print(f"\nPreferences: {len(persona.preferences)}")
        for p in persona.preferences:
            dom = p.get("domain") if isinstance(p, dict) else p.domain
            pref = p.get("preference") if isinstance(p, dict) else p.preference
            src = p.get("source") if isinstance(p, dict) else p.source
            print(f"  [{dom}] {pref}  (source: {src})")
    if persona.inferred_attributes:
        unreviewed = [a for a in persona.inferred_attributes if not (a.get("reviewed") if isinstance(a, dict) else False)]
        if unreviewed:
            print(f"\nInferred attributes awaiting review: {len(unreviewed)}")


def cmd_persona_init(args: argparse.Namespace) -> None:
    from project_store import PersonaStore
    store = PersonaStore()
    if store.exists():
        print("Persona already exists. Use 'aios persona show' to view it.")
        return
    persona = store.init(name=args.name)
    print(f"Persona initialised: {persona.id}")


def cmd_persona_set_value(args: argparse.Namespace) -> None:
    from project_store import PersonaStore
    store = PersonaStore()
    persona = store.add_value(value=args.value, priority=args.priority, category=args.category)
    print(f"Value added: [{args.priority}] {args.value}  ({args.category})")


def cmd_persona_add_fact(args: argparse.Namespace) -> None:
    from project_store import PersonaStore
    store = PersonaStore()
    persona = store.add_fact(
        statement=" ".join(args.statement),
        category=args.category,
        confidence=args.confidence,
    )
    print(f"Fact declared: {' '.join(args.statement)}")


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

    # -- project subcommands --------------------------------------------------
    proj = sub.add_parser("project", help="Manage projects")
    proj_sub = proj.add_subparsers(dest="proj_command", required=True)

    proj_add = proj_sub.add_parser("add", help="Add a new project")
    proj_add.add_argument("title", help="Project title")
    proj_add.add_argument("--type", choices=["project", "initiative", "maintenance"], default="project")
    proj_add.add_argument("--goal", default=None, help="Goal ID (GL-xxx)")
    proj_add.add_argument("--deadline", default=None, help="Target completion date (YYYY-MM-DD)")
    proj_add.add_argument("--weight", type=float, default=0.5, help="Priority weight (0.0–1.0)")
    proj_add.add_argument("--description", default=None, help="Short description")
    proj_add.set_defaults(func=cmd_project_add)

    proj_list = proj_sub.add_parser("list", help="List projects")
    proj_list.add_argument("--status", choices=["active", "all"], default="active")
    proj_list.set_defaults(func=cmd_project_list)

    proj_show = proj_sub.add_parser("show", help="Show project details")
    proj_show.add_argument("project_id", help="Project ID (PRJ-xxx)")
    proj_show.set_defaults(func=cmd_project_show)

    proj_touch = proj_sub.add_parser("touch", help="Record attention on a project")
    proj_touch.add_argument("project_id", help="Project ID (PRJ-xxx)")
    proj_touch.add_argument("--energy", choices=["high", "medium", "low"], default=None)
    proj_touch.set_defaults(func=cmd_project_touch)

    proj_update = proj_sub.add_parser("update", help="Update project status or health")
    proj_update.add_argument("project_id", help="Project ID (PRJ-xxx)")
    proj_update.add_argument("--status", choices=["draft", "active", "paused", "at_risk", "stalled", "completed", "cancelled", "abandoned"], default=None)
    proj_update.add_argument("--health", choices=["on_track", "at_risk", "blocked", "stalled"], default=None)
    proj_update.set_defaults(func=cmd_project_update)

    # -- commitment subcommands -----------------------------------------------
    commit = sub.add_parser("commit", help="Manage commitments")
    commit_sub = commit.add_subparsers(dest="commit_command", required=True)

    commit_add = commit_sub.add_parser("add", help="Add a commitment")
    commit_add.add_argument("description", help="What was promised")
    commit_add.add_argument("--deadline", required=True, help="Deadline (YYYY-MM-DD)")
    commit_add.add_argument("--project", default=None, help="Project ID (PRJ-xxx)")
    commit_add.add_argument("--promisee", default="self", help="Who the promise was made to")
    commit_add.add_argument("--weight", type=float, default=0.5, help="Importance weight (0.0–1.0)")
    commit_add.set_defaults(func=cmd_commit_add)

    commit_list = commit_sub.add_parser("list", help="List commitments")
    commit_list.add_argument("--status", choices=["active", "all"], default="active")
    commit_list.set_defaults(func=cmd_commit_list)

    commit_fulfill = commit_sub.add_parser("fulfill", help="Mark a commitment as fulfilled")
    commit_fulfill.add_argument("commitment_id", help="Commitment ID (CMT-xxx)")
    commit_fulfill.set_defaults(func=cmd_commit_fulfill)

    # -- persona subcommands --------------------------------------------------
    persona = sub.add_parser("persona", help="Manage operator persona")
    persona_sub = persona.add_subparsers(dest="persona_command", required=True)

    persona_show = persona_sub.add_parser("show", help="Show persona")
    persona_show.set_defaults(func=cmd_persona_show)

    persona_init = persona_sub.add_parser("init", help="Initialise persona")
    persona_init.add_argument("--name", default=None, help="Operator name")
    persona_init.set_defaults(func=cmd_persona_init)

    persona_val = persona_sub.add_parser("set-value", help="Declare a core value")
    persona_val.add_argument("value", help="Value statement")
    persona_val.add_argument("--priority", type=int, default=10, help="Priority (lower = higher priority)")
    persona_val.add_argument("--category", choices=["personal", "professional", "intellectual"], default="professional")
    persona_val.set_defaults(func=cmd_persona_set_value)

    persona_fact = persona_sub.add_parser("add-fact", help="Declare a fact about yourself")
    persona_fact.add_argument("statement", nargs="+", help="Fact statement")
    persona_fact.add_argument("--category", choices=["value", "belief", "preference", "habit", "constraint"], default="belief")
    persona_fact.add_argument("--confidence", choices=["high", "medium", "low"], default="medium")
    persona_fact.set_defaults(func=cmd_persona_add_fact)

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
