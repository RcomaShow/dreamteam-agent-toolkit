#!/usr/bin/env python3
"""Run the standalone Claude Code adapter installer from the repository root."""
from __future__ import annotations

from pathlib import Path
import runpy

INSTALLER = (
    Path(__file__).resolve().parents[1]
    / "adapters/claude-code/standalone/installer.py"
)


if __name__ == "__main__":
    runpy.run_path(str(INSTALLER), run_name="__main__")
