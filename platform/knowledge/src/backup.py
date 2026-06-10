"""
backup.py — Knowledge store backup and restore

Creates timestamped tar.gz archives of the knowledge store and restores
from them. All canonical knowledge must be backed up as specified in
knowledge/knowledge-architecture.md and ADR-003.

Capability: CAP-001 (Knowledge Management)
Defined by: ADR-003 — Knowledge Persistence Approach
"""

import hashlib
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from index_manager import STORE_DIR

DEFAULT_BACKUP_DIR = Path(__file__).parent.parent / "backups"


def _archive_name(dest_dir: Path) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = f"knowledge-store-{timestamp}"
    name = f"{base}.tar.gz"
    # Avoid overwriting an existing archive if two backups happen in the same second
    counter = 1
    while (dest_dir / name).exists():
        name = f"{base}-{counter}.tar.gz"
        counter += 1
    return name


def _checksum(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def backup(dest_dir: Optional[Path] = None) -> Path:
    """
    Create a timestamped tar.gz archive of the knowledge store.

    Returns the path to the created archive.
    """
    dest_dir = Path(dest_dir) if dest_dir else DEFAULT_BACKUP_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    archive_path = dest_dir / _archive_name(dest_dir)

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(STORE_DIR, arcname="store")

    checksum = _checksum(archive_path)
    checksum_file = Path(str(archive_path) + ".sha256")
    checksum_file.write_text(f"{checksum}  {archive_path.name}\n", encoding="utf-8")

    return archive_path


def restore(archive_path: Path, dest_dir: Optional[Path] = None) -> None:
    """
    Restore the knowledge store from a tar.gz archive.

    The existing store directory is replaced with the contents of the archive.
    A pre-restore backup of the current store is created automatically before
    any data is overwritten.

    Raises FileNotFoundError if the archive does not exist.
    Raises ValueError if the archive does not contain the expected 'store/' root.
    """
    archive_path = Path(archive_path)
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Verify checksum if a .sha256 file exists alongside the archive
    checksum_file = Path(str(archive_path) + ".sha256")
    if checksum_file.exists():
        expected = checksum_file.read_text(encoding="utf-8").split()[0]
        actual = _checksum(archive_path)
        if actual != expected:
            raise ValueError(
                f"Checksum mismatch for {archive_path.name}.\n"
                f"  Expected: {expected}\n"
                f"  Actual:   {actual}"
            )

    # Verify archive contains 'store/' at the root
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getnames()
        if not any(m == "store" or m.startswith("store/") for m in members):
            raise ValueError(
                f"Archive {archive_path.name} does not contain a 'store/' root. "
                "Is this a valid knowledge store backup?"
            )

    # Take a pre-restore backup of the current store
    pre_restore_dir = Path(dest_dir) if dest_dir else DEFAULT_BACKUP_DIR
    pre_restore_archive = backup(dest_dir=pre_restore_dir)
    print(f"Pre-restore backup created: {pre_restore_archive}")

    # Remove current store and extract archive
    if STORE_DIR.exists():
        shutil.rmtree(STORE_DIR)
    STORE_DIR.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=STORE_DIR.parent)

    print(f"Restore complete. Store restored from: {archive_path.name}")

