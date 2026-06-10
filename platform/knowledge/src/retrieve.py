"""
retrieve.py — Knowledge asset retrieval interface

Provides three retrieval modes as defined in knowledge/knowledge-architecture.md:
  1. Identifier-based  — direct lookup by KA-NNN ID
  2. Metadata-filtered — filter by status, domain, tags
  3. Full-text search  — keyword search over content and metadata

Capability: CAP-001 (Knowledge Management)
Defined by: ADR-003 — Knowledge Persistence Approach
"""

from pathlib import Path
from typing import Optional

import frontmatter

from index_manager import ASSETS_DIR, find_by_id, get_all_entries


def get_by_id(asset_id: str) -> Optional[dict]:
    """
    Retrieve a knowledge asset by its KA-NNN identifier.

    Returns a dict with 'metadata' and 'content' keys, or None if not found.
    """
    path = find_by_id(asset_id)
    if path is None:
        return None
    return _load_asset(path)


def list_assets(
    status: Optional[str] = None,
    domain: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> list[dict]:
    """
    Return index entries matching the given metadata filters.

    All filters are ANDed. Omitting a filter includes all values.
    Tags filter is satisfied if the asset has ALL of the specified tags.
    """
    entries = get_all_entries()
    results = []
    for entry in entries:
        if status and entry.get("status") != status:
            continue
        if domain and entry.get("domain") != domain:
            continue
        if tags:
            asset_tags = _get_tags_from_entry(entry)
            if not all(t in asset_tags for t in tags):
                continue
        results.append(entry)
    return results


def search(query: str, max_results: int = 50) -> list[dict]:
    """
    Full-text keyword search over asset content and metadata.

    Returns a list of matching index entries, ordered by relevance (simple
    hit-count ranking). Matching is case-insensitive.
    """
    query_lower = query.lower()
    terms = query_lower.split()
    scored: list[tuple[int, dict]] = []

    for path in sorted(ASSETS_DIR.rglob("*.md")):
        try:
            post = frontmatter.load(str(path))
            text = _searchable_text(post.metadata, post.content)
            score = sum(text.count(term) for term in terms)
            if score > 0:
                entry = {
                    "id": post.metadata.get("id", ""),
                    "title": post.metadata.get("title", path.stem),
                    "status": post.metadata.get("status", ""),
                    "domain": path.parent.name,
                    "path": str(path.relative_to(ASSETS_DIR.parent.parent)),
                    "version": post.metadata.get("version", 1),
                    "updated": str(post.metadata.get("updated", "")),
                    "_score": score,
                }
                scored.append((score, entry))
        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:max_results]]


def get_full_asset(asset_id: str) -> Optional[dict]:
    """Return the full asset (metadata + content) for a given ID."""
    return get_by_id(asset_id)


# --- helpers ---

def _load_asset(path: Path) -> dict:
    post = frontmatter.load(str(path))
    return {
        "metadata": dict(post.metadata),
        "content": post.content,
        "path": str(path),
    }


def _searchable_text(metadata: dict, content: str) -> str:
    """Combine metadata fields and content into a single searchable string."""
    parts = [
        str(metadata.get("title", "")),
        str(metadata.get("id", "")),
        " ".join(metadata.get("tags", [])),
        content,
    ]
    return " ".join(parts).lower()


def _get_tags_from_entry(entry: dict) -> list[str]:
    """Get tags for an entry, loading from file if necessary."""
    # The index does not store tags, so we load the file for tag filtering.
    path_str = entry.get("path", "")
    if not path_str:
        return []
    path = ASSETS_DIR.parent.parent / path_str
    if not path.exists():
        return []
    try:
        post = frontmatter.load(str(path))
        return post.metadata.get("tags", [])
    except Exception:
        return []
