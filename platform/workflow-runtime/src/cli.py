"""
cli.py — Workflow runtime command-line interface

Provides operator access to workflow execution, validation, and run records.

Usage:
  python src/cli.py run ../../workflows/WF-001-knowledge-ingest.yaml
  python src/cli.py validate ../../workflows/WF-001-knowledge-ingest.yaml
  python src/cli.py runs list
  python src/cli.py runs show <run-file.yaml>

Capability: CAP-004 (Workflow Orchestration)
"""

import sys
from pathlib import Path

import click
import yaml

sys.path.insert(0, str(Path(__file__).parent))

import executor as exec_mod
import run_log as run_log_mod
import validator as validator_mod


@click.group()
def cli():
    """AIOS Workflow Runtime — execute and inspect workflows."""


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("definition", type=click.Path(exists=True, path_type=Path))
@click.option("--var", multiple=True, metavar="KEY=VALUE",
              help="Input variable as KEY=VALUE. May be repeated.")
@click.option("--runs-dir", default=None, type=click.Path(path_type=Path),
              help="Directory for run records (overrides default).")
@click.option("--cwd", default=None, type=click.Path(path_type=Path),
              help="Working directory for step commands.")
@click.option("--yes", is_flag=True, default=False,
              help="Auto-approve all approval gates (use with caution).")
def run(definition: Path, var: tuple, runs_dir: Path, cwd: Path, yes: bool):
    """Execute a workflow from a YAML definition file."""
    inputs = {}
    for item in var:
        if "=" not in item:
            click.echo(f"Error: --var must be KEY=VALUE, got: {item!r}", err=True)
            sys.exit(1)
        k, v = item.split("=", 1)
        inputs[k.strip()] = v.strip()

    def approval_handler(step_id, step_name):
        if yes:
            click.echo(f"[AUTO-APPROVED] {step_id}: {step_name}", err=True)
            return True
        return exec_mod._cli_approval_prompt(step_id, step_name)

    try:
        run_record = exec_mod.run_workflow(
            definition,
            inputs=inputs,
            approval_handler=approval_handler,
            runs_dir=runs_dir,
            cwd=cwd,
        )
        status = run_record.get("status", "unknown")
        click.echo(f"Workflow {run_record['workflow_id']} completed: {status}")
        click.echo(f"Run record: {run_record['run_id']}")
    except exec_mod.WorkflowError as exc:
        click.echo(f"Workflow error: {exc}", err=True)
        sys.exit(1)
    except exec_mod.StepFailedError as exc:
        click.echo(f"Step failed: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("definition", type=click.Path(exists=True, path_type=Path))
def validate(definition: Path):
    """Validate a workflow definition file without executing it."""
    with definition.open("r", encoding="utf-8") as f:
        defn = yaml.safe_load(f)
    errors = validator_mod.validate(defn)
    if errors:
        click.echo(f"Validation failed ({len(errors)} error(s)):")
        for e in errors:
            click.echo(f"  - {e}")
        sys.exit(1)
    else:
        click.echo(f"Valid: {definition.name}")


# ---------------------------------------------------------------------------
# runs
# ---------------------------------------------------------------------------

@cli.group()
def runs():
    """Inspect workflow run records."""


@runs.command("list")
@click.option("--runs-dir", default=None, type=click.Path(path_type=Path))
def runs_list(runs_dir: Path):
    """List all workflow run records."""
    records = run_log_mod.list_runs(runs_dir)
    if not records:
        click.echo("No run records found.")
        return
    for p in records:
        run = run_log_mod.load_run(p)
        click.echo(
            f"{run.get('run_id',''):>45}  "
            f"{run.get('workflow_id',''):>8}  "
            f"{run.get('status',''):>10}  "
            f"{run.get('started_at','')}"
        )


@runs.command("show")
@click.argument("run_file", type=click.Path(exists=True, path_type=Path))
def runs_show(run_file: Path):
    """Show a workflow run record in detail."""
    run = run_log_mod.load_run(run_file)
    click.echo(yaml.dump(run, default_flow_style=False, allow_unicode=True), nl=False)


if __name__ == "__main__":
    cli()
