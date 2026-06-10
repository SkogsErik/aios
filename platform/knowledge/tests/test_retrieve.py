"""
test_retrieve.py — Tests for the retrieval interface.

Covers: get_by_id, list_assets (with filters), full-text search.
"""

from pathlib import Path

import frontmatter
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ingest(store_dir, tmp_path, name: str = "doc.md", content: str = "Body.",
            domain: str = "general", title: str = None, tags: list | None = None,
            status: str = "active") -> str:
    """Ingest a file and return the asset ID."""
    import ingest as ingest_mod
    source = tmp_path / name
    source.write_text(content, encoding="utf-8")
    dest = ingest_mod.ingest_file(source, domain=domain, title=title or name.replace(".md", "").title(),
                                   tags=tags or [])
    # Override status for test convenience
    post = frontmatter.load(str(dest))
    post.metadata["status"] = status
    dest.write_text(frontmatter.dumps(post), encoding="utf-8")
    import index_manager
    index_manager.rebuild_index()
    return post.metadata["id"]


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_returns_asset(store_dir, tmp_path):
    import retrieve
    asset_id = _ingest(store_dir, tmp_path, "test.md", "Hello world.")
    result = retrieve.get_by_id(asset_id)
    assert result is not None
    assert result["metadata"]["id"] == asset_id
    assert "Hello world." in result["content"]


def test_get_by_id_returns_none_for_unknown(store_dir, tmp_path):
    import retrieve
    assert retrieve.get_by_id("KA-999") is None


# ---------------------------------------------------------------------------
# list_assets
# ---------------------------------------------------------------------------

def test_list_assets_returns_all(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "a.md", domain="general")
    _ingest(store_dir, tmp_path, "b.md", domain="architecture")
    entries = retrieve.list_assets()
    assert len(entries) == 2


def test_list_assets_filter_by_status(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "active.md", status="active")
    _ingest(store_dir, tmp_path, "draft.md", status="draft")
    active = retrieve.list_assets(status="active")
    assert len(active) == 1
    assert active[0]["status"] == "active"


def test_list_assets_filter_by_domain(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "a.md", domain="general")
    _ingest(store_dir, tmp_path, "b.md", domain="architecture")
    arch = retrieve.list_assets(domain="architecture")
    assert len(arch) == 1
    assert arch[0]["domain"] == "architecture"


def test_list_assets_filter_by_tags(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "tagged.md", tags=["alpha", "beta"])
    _ingest(store_dir, tmp_path, "untagged.md", tags=[])
    results = retrieve.list_assets(tags=["alpha"])
    assert len(results) == 1


def test_list_assets_empty_store(store_dir, tmp_path):
    import retrieve
    assert retrieve.list_assets() == []


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

def test_search_finds_by_content(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "adr.md", content="Architecture Decision Record for the gateway.")
    _ingest(store_dir, tmp_path, "other.md", content="Something completely different.")
    results = retrieve.search("Architecture Decision")
    assert any("adr" in r.get("title", "").lower() or "architecture" in r.get("title", "").lower()
                or r.get("id") is not None for r in results)
    assert len(results) >= 1


def test_search_is_case_insensitive(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "doc.md", content="The MODEL GATEWAY handles all AI calls.")
    results = retrieve.search("model gateway")
    assert len(results) >= 1


def test_search_no_results(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "doc.md", content="Hello world.")
    results = retrieve.search("xyzzy_not_found")
    assert results == []


def test_search_scores_higher_for_more_hits(store_dir, tmp_path):
    import retrieve
    _ingest(store_dir, tmp_path, "many.md", content="knowledge knowledge knowledge store.")
    _ingest(store_dir, tmp_path, "few.md", content="knowledge base.")
    results = retrieve.search("knowledge")
    assert results[0]["_score"] >= results[1]["_score"]
