"""
cli.py — Model gateway command-line interface

Provides operator access to the model gateway and audit log.

Usage:
  python src/cli.py query "What is the AIOS vision?"
  python src/cli.py audit tail
  python src/cli.py audit filter --caller WF-001

Capability: CAP-003 (AI and Model Management)
"""

import sys
import json
from pathlib import Path

import click
import yaml

sys.path.insert(0, str(Path(__file__).parent))

import audit_log as audit_mod
from config_loader import get_audit_log_path, load_config


@click.group()
def cli():
    """AIOS Model Gateway — send model requests and inspect audit log."""


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("prompt")
@click.option("--model", default=None, help="LiteLLM model identifier (overrides config default).")
@click.option("--caller-id", default="operator", show_default=True,
              help="Traceability ID for the caller.")
@click.option("--max-tokens", default=None, type=int, help="Maximum completion tokens.")
@click.option("--temperature", default=None, type=float, help="Sampling temperature.")
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path),
              help="Path to gateway-config.yaml (overrides default).")
def query(prompt: str, model: str, caller_id: str, max_tokens: int,
          temperature: float, config_path: Path):
    """Send a completion request through the model gateway."""
    # Import here to avoid requiring litellm at CLI import time
    import gateway as gw
    try:
        response = gw.complete(
            prompt,
            model=model,
            caller_id=caller_id,
            max_tokens=max_tokens,
            temperature=temperature,
            config_path=config_path,
        )
        click.echo(response.content)
        click.echo(f"\n[{response.call_id} | {response.model} | {response.latency_ms}ms]", err=True)
    except gw.GatewayError as exc:
        click.echo(f"Gateway error ({exc.status}): {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------

@cli.group()
def audit():
    """Inspect the model gateway audit log."""


@audit.command("tail")
@click.option("--n", default=20, show_default=True, help="Number of entries to show.")
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path),
              help="Path to gateway-config.yaml.")
def audit_tail(n: int, config_path: Path):
    """Show the most recent audit log entries."""
    cfg = load_config(config_path)
    log_path = get_audit_log_path(cfg)
    entries = audit_mod.tail_entries(log_path, n=n)
    if not entries:
        click.echo("No audit entries found.")
        return
    _print_entries(entries)


@audit.command("filter")
@click.option("--caller", default=None, help="Filter by caller_id.")
@click.option("--status", default=None, help="Filter by status (success, error, ...).")
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path),
              help="Path to gateway-config.yaml.")
def audit_filter(caller: str, status: str, config_path: Path):
    """Filter audit log entries by caller or status."""
    cfg = load_config(config_path)
    log_path = get_audit_log_path(cfg)
    entries = audit_mod.filter_entries(log_path, caller_id=caller, status=status)
    if not entries:
        click.echo("No matching audit entries.")
        return
    _print_entries(entries)


@audit.command("stats")
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path),
              help="Path to gateway-config.yaml.")
def audit_stats(config_path: Path):
    """Show summary statistics for the audit log."""
    cfg = load_config(config_path)
    log_path = get_audit_log_path(cfg)
    entries = audit_mod.read_entries(log_path)
    if not entries:
        click.echo("No audit entries found.")
        return

    total = len(entries)
    success = sum(1 for e in entries if e.get("status") == "success")
    errors = sum(1 for e in entries if e.get("status") == "error")
    total_tokens = sum(e.get("total_tokens") or 0 for e in entries)
    total_cost = sum(e.get("cost_usd") or 0.0 for e in entries)
    avg_latency = sum(e.get("latency_ms", 0) for e in entries) / total

    click.echo(f"Total calls:   {total}")
    click.echo(f"Successful:    {success}")
    click.echo(f"Errors:        {errors}")
    click.echo(f"Total tokens:  {total_tokens}")
    click.echo(f"Total cost:    ${total_cost:.4f}")
    click.echo(f"Avg latency:   {avg_latency:.0f}ms")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_entries(entries: list[dict]) -> None:
    for e in entries:
        status_marker = "✓" if e.get("status") == "success" else "✗"
        click.echo(
            f"{status_marker} {e.get('timestamp','')}  "
            f"{e.get('call_id',''):>8}  "
            f"{e.get('caller_id',''):>12}  "
            f"{e.get('model',''):<25}  "
            f"{e.get('total_tokens') or '?':>6} tok  "
            f"{e.get('latency_ms',0):>5}ms  "
            f"{e.get('status','')}"
        )
        if e.get("error"):
            click.echo(f"  ERROR: {e['error']}", err=True)


if __name__ == "__main__":
    cli()
