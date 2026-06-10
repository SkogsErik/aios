"""
platform/executive-daemon/__main__.py — Entry point for `python -m executive-daemon`.

Usage:
  python -m platform.executive-daemon start
  python -m platform.executive-daemon status
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

from cli import main

main()
