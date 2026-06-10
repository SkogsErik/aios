"""
cli.py — Knowledge platform command-line interface

Entry point for all knowledge management operations. Wraps the ingestion,
retrieval, index, and backup modules behind a consistent CLI.

Usage:
  python src/cli.py --help

Capability: CAP-001 (Knowledge Management)
"""

import sys
from pathlib import Path

import click
import yaml

# Ensure src/ is on the import path when run directly
sys.path.insert(0, str(Path(__file__).parent))

import backup as backup_mod
import ingest as ingest_mod
import index_manager
import retrieve as retrieve_mod


@click.group()
def cli():
    """AIOS Knowledge Platform — manage knowledge assets."""


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--domain", default="general", show_default=True,
              help="Domain sub-directory to store the asset in.")
@click.option("--title", default=None,
              help="Override the asset title (defaults to front-matter title or filename).")
@click.option("--author", default="operator", show_default=True,
              help="Author identifier recorded in asset provenance.")
@click.option("--tags", default="", show_default=False,
              help="Comma-separated list of tags to add to the asset.")
def ingest(file: Path, domain: str, title: str, author: str, tags: str):
    """Ingest a Markdown file into the knowledge store."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        dest = ingest_mod.ingest_file(
            source_path=file,
            domain=domain,
            title=title,
            author=author,
            origin="manual",
            tags=tag_list,
        )
        click.echo(f"Ingested: {dest}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("asset_id")
@click.option("--content/--no-content", default=True, show_default=True,
              help="Whether to print the full asset content.")
def get(asset_id: str, content: bool):
    """Retrieve a knowledge asset by its KA-NNN identifier."""
    asset = retrieve_mod.get_by_id(asset_id)
    if asset is None:
        click.echo(f"Asset not found: {asset_id}", err=True)
        sys.exit(1)
    click.echo("--- metadata ---")
    click.echo(yaml.dump(asset["metadata"], default_flow_style=False, allow_unicode=True), nl=False)
    if content:
        click.echo("--- content ---")
        click.echo(asset["content"])


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

@cli.command("list")
@click.option("--status", default=None,
              help="Filter by lifecycle status (draft, active, review, deprecated, archived).")
@click.option("--domain", default=None, help="Filter by domain.")
@click.option("--tags", default="", help="Comma-separated tags (asset must have ALL listed tags).")
def list_assets(status: str, domain: str, tags: str):
    """List knowledge assets, optionally filtered by metadata."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    entries = retrieve_mod.list_assets(status=status, domain=domain, tags=tag_list or None)
    if not entries:
        click.echo("No assets found.")
        return
    # Tabular output
    col_id = max(len(e.get("id", "")) for e in entries)
    col_status = max(len(e.get("status", "")) for e in entries)
    col_domain = max(len(e.get("domain", "")) for e in entries)
    header = f"{'ID':<{max(col_id,4)}}  {'STATUS':<{max(col_status,6)}}  {'DOMAIN':<{max(col_domain,6)}}  TITLE"
    click.echo(header)
    click.echo("-" * (len(header) + 20))
    for e in entries:
        click.echo(
            f"{e.get('id',''):<{max(col_id,4)}}  "
            f"{e.get('status',''):<{max(col_status,6)}}  "
            f"{e.get('domain',''):<{max(col_domain,6)}}  "
            f"{e.get('title','')}"
        )


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("query")
@click.option("--max-results", default=20, show_default=True)
def search(query: str, max_results: int):
    """Full-text keyword search across asset content and metadata."""
    results = retrieve_mod.search(query, max_results=max_results)
    if not results:
        click.echo("No results found.")
        return
    click.echo(f"Found {len(results)} result(s) for '{query}':\n")
    for r in results:
        click.echo(f"  {r['id']:>8}  [{r.get('status','')}]  {r.get('title','')}  (score: {r['_score']})")


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------

@cli.group()
def index():
    """Manage the knowledge asset index."""


@index.command("rebuild")
def index_rebuild():
    """Rebuild the index by scanning all asset files."""
    count = index_manager.rebuild_index()
    click.echo(f"Index rebuilt: {count} asset(s) indexed.")


# ---------------------------------------------------------------------------
# backup / restore
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--dest", default=None, type=click.Path(path_type=Path),
              help="Destination directory for the backup archive. Defaults to platform/knowledge/backups/.")
def backup(dest: Path):
    """Create a timestamped backup of the knowledge store."""
    try:
        archive = backup_mod.backup(dest_dir=dest)
        click.echo(f"Backup created: {archive}")
        checksum_file = Path(str(archive) + ".sha256")
        if checksum_file.exists():
            click.echo(f"Checksum:       {checksum_file}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("archive", type=click.Path(exists=True, path_type=Path))
@click.option("--backup-dest", default=None, type=click.Path(path_type=Path),
              help="Directory to store the pre-restore backup. Defaults to platform/knowledge/backups/.")
def restore(archive: Path, backup_dest: Path):
    """Restore the knowledge store from a backup archive.

    A pre-restore backup is created automatically before any data is overwritten.
    """
    try:
        backup_mod.restore(archive_path=archive, dest_dir=backup_dest)
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
