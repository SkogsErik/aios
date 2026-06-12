"""
test_backup.py — Tests for backup and restore procedures.

Satisfies Phase 3 exit criterion: "Backup and restore procedures are
documented and tested."

Covers:
  - backup creates a valid tar.gz archive with a SHA-256 checksum
  - archive contains the expected store/ structure
  - restore replaces the store from the archive
  - restore verifies the checksum when a .sha256 file is present
  - restore creates a pre-restore backup automatically
  - restore raises ValueError for a tampered archive
  - restore raises ValueError for an archive with wrong root
"""

import hashlib
import tarfile
from pathlib import Path

from frontmatter_util import Post as _FmPost, dumps as _fm_dumps
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_asset(assets_dir: Path, domain: str, filename: str, content: str = "Body.") -> Path:
    domain_dir = assets_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    path = domain_dir / filename
    post = _FmPost(content, id="KA-001", title="Test", status="draft",
                    created="2026-01-01", updated="2026-01-01",
                    author="operator", origin="manual", version=1,
                    provenance={"source_uri": None, "ingested_via": None},
                    tags=[], related=[])
    path.write_text(_fm_dumps(post), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# backup
# ---------------------------------------------------------------------------

def test_backup_creates_archive(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=dest)
    assert archive.exists()
    assert archive.suffix == ".gz"
    assert "knowledge-store-" in archive.name


def test_backup_creates_checksum_file(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=dest)
    checksum_file = Path(str(archive) + ".sha256")
    assert checksum_file.exists()


def test_backup_checksum_is_valid(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=dest)
    checksum_file = Path(str(archive) + ".sha256")

    expected_hash = checksum_file.read_text(encoding="utf-8").split()[0]
    h = hashlib.sha256()
    with archive.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    assert h.hexdigest() == expected_hash


def test_backup_archive_contains_store_root(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=dest)
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getnames()
    assert any(m == "store" or m.startswith("store/") for m in members)


def test_backup_archive_contains_asset_file(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=dest)
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getnames()
    assert any("KA-001-test.md" in m for m in members)


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------

def test_restore_replaces_store(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    # Create an asset and back up
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-original.md", "Original content.")
    backup_dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=backup_dest)

    # Modify the store after backup
    new_asset = index_manager.ASSETS_DIR / "general" / "KA-002-new.md"
    new_asset.write_text("New content.", encoding="utf-8")
    assert new_asset.exists()

    # Restore from backup
    backup_mod.restore(archive_path=archive, dest_dir=backup_dest)

    # KA-002 should be gone; KA-001 should be present
    assert not new_asset.exists()
    assert (index_manager.ASSETS_DIR / "general" / "KA-001-original.md").exists()


def test_restore_creates_pre_restore_backup(store_dir, tmp_path, capsys):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    backup_dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=backup_dest)
    backup_mod.restore(archive_path=archive, dest_dir=backup_dest)
    captured = capsys.readouterr()
    assert "Pre-restore backup created" in captured.out
    # Should have at least 2 archives: the original + the pre-restore backup
    archives = list(backup_dest.glob("*.tar.gz"))
    assert len(archives) >= 2


def test_restore_raises_for_missing_archive(store_dir, tmp_path):
    import backup as backup_mod
    with pytest.raises(FileNotFoundError):
        backup_mod.restore(archive_path=tmp_path / "nonexistent.tar.gz")


def test_restore_raises_for_tampered_archive(store_dir, tmp_path):
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    backup_dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=backup_dest)

    # Tamper with the archive
    archive.write_bytes(archive.read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="Checksum mismatch"):
        backup_mod.restore(archive_path=archive, dest_dir=backup_dest)


def test_restore_raises_for_wrong_root(store_dir, tmp_path):
    import backup as backup_mod
    backup_dest = tmp_path / "backups"
    backup_dest.mkdir(parents=True)

    # Create an archive with a wrong root directory
    bad_archive = backup_dest / "bad.tar.gz"
    with tarfile.open(bad_archive, "w:gz") as tar:
        dummy = tmp_path / "dummy.txt"
        dummy.write_text("not a knowledge store")
        tar.add(dummy, arcname="wrong_root/dummy.txt")

    with pytest.raises(ValueError, match="does not contain a 'store/' root"):
        backup_mod.restore(archive_path=bad_archive, dest_dir=backup_dest)


def test_restore_succeeds_without_checksum_file(store_dir, tmp_path):
    """Restore should succeed when no .sha256 file exists (checksum step is skipped)."""
    import backup as backup_mod, index_manager
    _write_asset(index_manager.ASSETS_DIR, "general", "KA-001-test.md")
    backup_dest = tmp_path / "backups"
    archive = backup_mod.backup(dest_dir=backup_dest)

    # Remove the checksum file
    checksum_file = Path(str(archive) + ".sha256")
    checksum_file.unlink()

    # Restore should still work
    backup_mod.restore(archive_path=archive, dest_dir=backup_dest)
    assert (index_manager.ASSETS_DIR / "general" / "KA-001-test.md").exists()
