"""
test_index_manager.py — Tests for index_manager module.

Covers: rebuild_index, next_asset_id, find_by_id, add_or_update_entry,
get_all_entries.
"""

from pathlib import Path

import frontmatter
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_asset(assets_dir: Path, domain: str, filename: str, meta: dict, content: str = "") -> Path:
    """Write a minimal knowledge asset file under assets_dir/<domain>/."""
    domain_dir = assets_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    path = domain_dir / filename
    post = frontmatter.Post(content, **meta)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# rebuild_index
# ---------------------------------------------------------------------------

def test_rebuild_index_empty_store(store_dir):
    import index_manager
    count = index_manager.rebuild_index()
    assert count == 0
    entries = index_manager.get_all_entries()
    assert entries == []


def test_rebuild_index_single_asset(store_dir):
    import index_manager
    _write_asset(
        index_manager.ASSETS_DIR,
        "general",
        "KA-001-test-asset.md",
        {"id": "KA-001", "title": "Test Asset", "status": "draft",
         "created": "2026-01-01", "updated": "2026-01-01",
         "author": "operator", "origin": "manual", "version": 1,
         "provenance": {"source_uri": None, "ingested_via": "PIPELINE-001"},
         "tags": [], "related": []},
        "Asset content.",
    )
    count = index_manager.rebuild_index()
    assert count == 1
    entries = index_manager.get_all_entries()
    assert len(entries) == 1
    assert entries[0]["id"] == "KA-001"
    assert entries[0]["title"] == "Test Asset"
    assert entries[0]["domain"] == "general"


def test_rebuild_index_multiple_domains(store_dir):
    import index_manager
    for i, domain in enumerate(["general", "architecture", "domain"], start=1):
        _write_asset(
            index_manager.ASSETS_DIR,
            domain,
            f"KA-{i:03d}-asset.md",
            {"id": f"KA-{i:03d}", "title": f"Asset {i}", "status": "active",
             "created": "2026-01-01", "updated": "2026-01-01",
             "author": "operator", "origin": "manual", "version": 1,
             "provenance": {"source_uri": None, "ingested_via": None},
             "tags": [], "related": []},
        )
    count = index_manager.rebuild_index()
    assert count == 3
    ids = {e["id"] for e in index_manager.get_all_entries()}
    assert ids == {"KA-001", "KA-002", "KA-003"}


def test_rebuild_index_sorts_by_id(store_dir):
    import index_manager
    for num in [3, 1, 2]:
        _write_asset(
            index_manager.ASSETS_DIR,
            "general",
            f"KA-{num:03d}-asset.md",
            {"id": f"KA-{num:03d}", "title": f"Asset {num}", "status": "draft",
             "created": "2026-01-01", "updated": "2026-01-01",
             "author": "operator", "origin": "manual", "version": 1,
             "provenance": {"source_uri": None, "ingested_via": None},
             "tags": [], "related": []},
        )
    index_manager.rebuild_index()
    entries = index_manager.get_all_entries()
    assert [e["id"] for e in entries] == ["KA-001", "KA-002", "KA-003"]


# ---------------------------------------------------------------------------
# next_asset_id
# ---------------------------------------------------------------------------

def test_next_asset_id_empty_store(store_dir):
    import index_manager
    assert index_manager.next_asset_id() == "KA-001"


def test_next_asset_id_increments(store_dir):
    import index_manager
    _write_asset(
        index_manager.ASSETS_DIR, "general", "KA-005-asset.md",
        {"id": "KA-005", "title": "Asset", "status": "draft",
         "created": "2026-01-01", "updated": "2026-01-01",
         "author": "operator", "origin": "manual", "version": 1,
         "provenance": {"source_uri": None, "ingested_via": None},
         "tags": [], "related": []},
    )
    index_manager.rebuild_index()
    assert index_manager.next_asset_id() == "KA-006"


def test_next_asset_id_uses_asset_files_when_index_stale(store_dir):
    import index_manager
    # Write an asset file without rebuilding the index
    _write_asset(
        index_manager.ASSETS_DIR, "general", "KA-010-asset.md",
        {"id": "KA-010", "title": "Asset", "status": "draft",
         "created": "2026-01-01", "updated": "2026-01-01",
         "author": "operator", "origin": "manual", "version": 1,
         "provenance": {"source_uri": None, "ingested_via": None},
         "tags": [], "related": []},
    )
    # Index is still empty, but next_asset_id should scan the files too
    assert index_manager.next_asset_id() == "KA-011"


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------

def test_find_by_id_returns_path(store_dir):
    import index_manager
    expected_path = _write_asset(
        index_manager.ASSETS_DIR, "general", "KA-001-test.md",
        {"id": "KA-001", "title": "Test", "status": "draft",
         "created": "2026-01-01", "updated": "2026-01-01",
         "author": "operator", "origin": "manual", "version": 1,
         "provenance": {"source_uri": None, "ingested_via": None},
         "tags": [], "related": []},
    )
    assert index_manager.find_by_id("KA-001") == expected_path


def test_find_by_id_returns_none_when_missing(store_dir):
    import index_manager
    assert index_manager.find_by_id("KA-999") is None


# ---------------------------------------------------------------------------
# add_or_update_entry / get_all_entries
# ---------------------------------------------------------------------------

def test_add_entry(store_dir):
    import index_manager
    entry = {"id": "KA-001", "title": "New", "status": "draft", "domain": "general",
             "path": "store/assets/general/KA-001-new.md", "version": 1, "updated": "2026-01-01"}
    index_manager.add_or_update_entry("KA-001", entry)
    entries = index_manager.get_all_entries()
    assert len(entries) == 1
    assert entries[0]["id"] == "KA-001"


def test_update_entry(store_dir):
    import index_manager
    entry_v1 = {"id": "KA-001", "title": "V1", "status": "draft", "domain": "general",
                "path": "store/assets/general/KA-001.md", "version": 1, "updated": "2026-01-01"}
    entry_v2 = {**entry_v1, "title": "V2", "version": 2}
    index_manager.add_or_update_entry("KA-001", entry_v1)
    index_manager.add_or_update_entry("KA-001", entry_v2)
    entries = index_manager.get_all_entries()
    assert len(entries) == 1
    assert entries[0]["title"] == "V2"
    assert entries[0]["version"] == 2
