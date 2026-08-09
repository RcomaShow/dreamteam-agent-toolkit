#!/usr/bin/env python3
"""Install the DreamTeam 0.5 Codex adapter without silent overwrites."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
PROJECT_SOURCE = ROOT / "adapters/codex/AGENTS.md"
SKILL_SOURCE = ROOT / "adapters/codex/skills/dreamteam-run/SKILL.md"


def _copy_atomic(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".dreamteam.tmp")
    shutil.copyfile(source, temporary)
    temporary.replace(target)


def install_project(
    project_root: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("project root must be an existing directory")
    target = root / "AGENTS.md"
    if target.is_symlink():
        raise PermissionError("AGENTS.md may not be a symlink")
    if target.exists() and not force:
        raise FileExistsError(
            "AGENTS.md already exists; merge adapters/codex/AGENTS.md manually or rerun with --force"
        )
    if target.exists() and not target.is_file():
        raise PermissionError("AGENTS.md target must be a regular file")
    if not dry_run:
        _copy_atomic(PROJECT_SOURCE, target)
    return target


def install_user_skill(
    codex_home: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    home = codex_home.expanduser().resolve()
    target = home / "skills/dreamteam-run/SKILL.md"
    if target.is_symlink():
        raise PermissionError("DreamTeam SKILL.md may not be a symlink")
    if target.exists() and not force:
        raise FileExistsError("DreamTeam Codex skill already exists; use --force to replace it")
    if target.exists() and not target.is_file():
        raise PermissionError("DreamTeam skill target must be a regular file")
    if not dry_run:
        _copy_atomic(SKILL_SOURCE, target)
    return target


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("project", "user"), required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.scope == "project":
        target = install_project(
            args.project_root,
            force=args.force,
            dry_run=args.dry_run,
        )
    else:
        target = install_user_skill(
            args.codex_home,
            force=args.force,
            dry_run=args.dry_run,
        )
    action = "would install" if args.dry_run else "installed"
    print(f"{action}: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
