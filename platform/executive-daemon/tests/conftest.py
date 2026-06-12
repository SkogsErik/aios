"""
conftest.py — Shared pytest fixtures for executive daemon tests.
Patches sys.path so that src/ modules and wyrd/ are importable.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

# Wyrd subsystem (ADR-012) — identity stores live in wyrd/src/
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_WYRD_SRC = _REPO_ROOT / "wyrd" / "src"
if str(_WYRD_SRC) not in sys.path:
    sys.path.insert(0, str(_WYRD_SRC))
