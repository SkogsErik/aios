"""
ingest.py — Knowledge asset ingestion pipeline

Ingests a Markdown file (with or without existing YAML front-matter) into the
knowledge store as a versioned, provenance-tracked knowledge asset.

Ingestion pipeline ID: PIPELINE-001 (Markdown ingestion)
Capability: CAP-001 (Knowledge Management)
Defined by: ADR-003 — Knowledge Persistence Approach
"""

import re
from datetime import date
from pathlib import Path
from typing import Optional

import frontmatter
import yaml

from index_manager import ASSETS_DIR, _domain_for, add_or_update_entry, find_by_id, next_asset_id

REQUIRED_FIELDS = [
    "id", "title", "status", "created", "updated",
    "author", "origin", "version", "provenance", "tags", "related",
]


def _slugify(text: str) -> str:
    """Return a safe, lowercase filename slug from a title string."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:60]  # cap slug length


def _ensure_required_fields(
    meta: dict,
    asset_id: str,
    title: str,
    author: str,
    origin: str,
    tags: list[str],
) -> dict:
    """Return metadata dict with all required fields populated."""
    today = date.today().isoformat()
    meta.setdefault("id", asset_id)
    meta.setdefault("title", title)
    meta.setdefault("status", "draft")
    meta.setdefault("created", today)
    meta["updated"] = today
    meta.setdefault("author", author)
    meta.setdefault("origin", origin)
    if "version" not in meta:
        meta["version"] = 1
    else:
        meta["version"] = int(meta["version"]) + 1
    if "provenance" not in meta or not isinstance(meta["provenance"], dict):
        meta["provenance"] = {"source_uri": None, "ingested_via": "PIPELINE-001"}
    else:
        meta["provenance"].setdefault("source_uri", None)
        meta["provenance"].setdefault("ingested_via", "PIPELINE-001")
    if tags and not meta.get("tags"):
        meta["tags"] = tags
    elif "tags" not in meta:
        meta["tags"] = []
    meta.setdefault("related", [])
    return meta


def ingest_file(
    source_path: Path,
    domain: str = "general",
    title: Optional[str] = None,
    author: str = "operator",
    origin: str = "manual",
    tags: Optional[list[str]] = None,
) -> Path:
    """
    Ingest a Markdown file into the knowledge store.

    Returns the path to the created or updated asset file.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    # Parse existing front-matter (if any)
    post = frontmatter.load(str(source_path))
    meta = dict(post.metadata)
    content = post.content

    # Determine the asset ID
    existing_id = meta.get("id")
    if existing_id and existing_id.startswith("KA-"):
        asset_id = existing_id
    else:
        asset_id = next_asset_id()

    # Resolve title: argument > front-matter > filename stem
    resolved_title = title or meta.get("title") or source_path.stem.replace("-", " ").replace("_", " ").title()

    # Populate all required metadata fields
    meta = _ensure_required_fields(
        meta=meta,
        asset_id=asset_id,
        title=resolved_title,
        author=author,
        origin=origin,
        tags=tags or [],
    )
    meta["provenance"]["source_uri"] = str(source_path.resolve())

    # Determine the destination path within the store
    domain_dir = ASSETS_DIR / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(resolved_title)
    filename = f"{asset_id}-{slug}.md"
    dest_path = domain_dir / filename

    # If the asset already exists at a different path, remove the old file
    if existing_id:
        old_path = find_by_id(existing_id)
        if old_path and old_path != dest_path:
            old_path.unlink(missing_ok=True)

    # Write the asset file with updated front-matter
    new_post = frontmatter.Post(content, **meta)
    with dest_path.open("w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(new_post))

    # Update the index
    index_entry = {
        "id": asset_id,
        "title": resolved_title,
        "status": meta["status"],
        "domain": domain,
        "path": str(dest_path.relative_to(ASSETS_DIR.parent.parent)),
        "version": meta["version"],
        "updated": meta["updated"],
    }
    add_or_update_entry(asset_id, index_entry)

    return dest_path
