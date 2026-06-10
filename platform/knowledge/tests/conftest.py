"""
conftest.py — Shared pytest fixtures for knowledge platform tests.

Fixtures patch the module-level path constants in index_manager and all
modules that import directly from it (ingest, retrieve, backup), so that
all tests operate on isolated temporary directories, leaving the real
knowledge store untouched.
"""

import sys
from pathlib import Path

import pytest

# Ensure src/ is importable
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture()
def store_dir(tmp_path, monkeypatch):
    """
    Return a temporary knowledge store directory structure and patch all
    path constants in index_manager, ingest, retrieve, and backup to
    point to it.

    Layout created:
        tmp_path/
          store/
            assets/
              general/
            index/
              assets.yaml
    """
    import index_manager
    import ingest as ingest_mod
    import retrieve as retrieve_mod
    import backup as backup_mod

    store = tmp_path / "store"
    assets = store / "assets"
    general = assets / "general"
    index_dir = store / "index"

    for d in (general, index_dir):
        d.mkdir(parents=True)

    index_file = index_dir / "assets.yaml"
    index_file.write_text("assets: []\n", encoding="utf-8")

    # Patch index_manager (functions defined here look up these globals at call time)
    monkeypatch.setattr(index_manager, "STORE_DIR", store)
    monkeypatch.setattr(index_manager, "ASSETS_DIR", assets)
    monkeypatch.setattr(index_manager, "INDEX_FILE", index_file)

    # Patch the names imported into ingest, retrieve, and backup at module load
    # (Python copies the reference at import time; monkeypatching the source
    # module does not update these local bindings)
    monkeypatch.setattr(ingest_mod, "ASSETS_DIR", assets)
    monkeypatch.setattr(retrieve_mod, "ASSETS_DIR", assets)
    monkeypatch.setattr(backup_mod, "STORE_DIR", store)
    monkeypatch.setattr(backup_mod, "DEFAULT_BACKUP_DIR", tmp_path / "backups")

    yield store
