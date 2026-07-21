#!/usr/bin/env python3
"""Create a DreamTeam project configuration through the bundled runtime."""
from __future__ import annotations

from pathlib import Path
import sys

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))

from dreamteam.operations import main as operations_main


if __name__ == "__main__":
    raise SystemExit(operations_main(["init", *sys.argv[1:]]))
