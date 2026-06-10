"""
test_ingest.py — Tests for the ingestion pipeline.

Covers: ingest_file with and without front-matter, ID assignment,
versioning, provenance capture, domain routing.
"""

from pathlib import Path

import frontmatter
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_source(tmp_path: Path, name: str, content: str = "Body text.", meta: dict | None = None) -> Path:
    """Write a source Markdown file (with optional front-matter) to tmp_path."""
    path = tmp_path / name
    if meta:
        post = frontmatter.Post(content, **meta)
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Basic ingestion
# ---------------------------------------------------------------------------

def test_ingest_plain_markdown_assigns_id(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "doc.md", "Hello world.")
    dest = ingest.ingest_file(source, domain="general")
    assert dest.exists()
    post = frontmatter.load(str(dest))
    assert post.metadata["id"] == "KA-001"
    assert post.metadata["version"] == 1


def test_ingest_preserves_existing_front_matter(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "doc.md", "Content.", meta={"title": "My Doc", "status": "active"})
    dest = ingest.ingest_file(source)
    post = frontmatter.load(str(dest))
    assert post.metadata["title"] == "My Doc"
    assert post.metadata["status"] == "active"


def test_ingest_title_argument_overrides_front_matter(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "doc.md", "Content.", meta={"title": "Old Title"})
    dest = ingest.ingest_file(source, title="New Title")
    post = frontmatter.load(str(dest))
    assert post.metadata["title"] == "New Title"


def test_ingest_title_defaults_to_filename(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "my-research-notes.md")
    dest = ingest.ingest_file(source)
    post = frontmatter.load(str(dest))
    assert post.metadata["title"] == "My Research Notes"


def test_ingest_captures_provenance(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "doc.md")
    dest = ingest.ingest_file(source, author="test-operator", origin="manual")
    post = frontmatter.load(str(dest))
    assert post.metadata["author"] == "test-operator"
    assert post.metadata["origin"] == "manual"
    assert post.metadata["provenance"]["source_uri"] == str(source.resolve())
    assert post.metadata["provenance"]["ingested_via"] == "PIPELINE-001"


def test_ingest_tags_applied(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "doc.md")
    dest = ingest.ingest_file(source, tags=["research", "draft"])
    post = frontmatter.load(str(dest))
    assert "research" in post.metadata["tags"]
    assert "draft" in post.metadata["tags"]


def test_ingest_domain_routing(store_dir, tmp_path):
    import ingest, index_manager
    source = _write_source(tmp_path, "doc.md")
    dest = ingest.ingest_file(source, domain="architecture")
    assert dest.parent == index_manager.ASSETS_DIR / "architecture"


def test_ingest_adds_entry_to_index(store_dir, tmp_path):
    import ingest, index_manager
    source = _write_source(tmp_path, "doc.md")
    ingest.ingest_file(source)
    entries = index_manager.get_all_entries()
    assert len(entries) == 1
    assert entries[0]["id"] == "KA-001"


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def test_ingest_increments_version_on_re_ingest(store_dir, tmp_path):
    import ingest
    source = _write_source(tmp_path, "doc.md", "Version 1.")
    dest_v1 = ingest.ingest_file(source)
    post_v1 = frontmatter.load(str(dest_v1))
    assert post_v1.metadata["version"] == 1

    # Re-ingest the same file (now it has front-matter with the KA ID)
    dest_v2 = ingest.ingest_file(dest_v1)
    post_v2 = frontmatter.load(str(dest_v2))
    assert post_v2.metadata["version"] == 2


def test_ingest_sequential_id_assignment(store_dir, tmp_path):
    import ingest
    for i, name in enumerate(["a.md", "b.md", "c.md"], start=1):
        source = _write_source(tmp_path, name, f"Document {i}.")
        dest = ingest.ingest_file(source)
        post = frontmatter.load(str(dest))
        assert post.metadata["id"] == f"KA-{i:03d}"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_ingest_missing_file_raises(store_dir, tmp_path):
    import ingest
    with pytest.raises(FileNotFoundError):
        ingest.ingest_file(tmp_path / "nonexistent.md")
