#!/usr/bin/env python3
"""Install the DreamTeam 0.5 Codex adapter without silent overwrites."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
PROJECT_SOURCE = ROOT / "adapters/codex/AGENTS.md"
SKILL_SOURCE = ROOT / "adapters/codex/skills/dreamteam-run/SKILL.md"


def _prepare_parent(root: Path, parent: Path, *, create: bool) -> None:
    """Reject symlinked/non-directory components below the selected install root."""
    try:
        relative = parent.relative_to(root)
    except ValueError as exc:
        raise PermissionError("adapter target escapes the selected install root") from exc

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PermissionError("adapter target parent may not traverse symlinks")
        if current.exists() and not current.is_dir():
            raise PermissionError("adapter target parent component must be a directory")

    if not create:
        return
    parent.mkdir(parents=True, exist_ok=True)

    # Recheck after creation so pre-existing or concurrently replaced parent
    # components are not accepted merely because mkdir(exist_ok=True) returned.
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink() or not current.is_dir():
            raise PermissionError("adapter target parent changed during installation")
    try:
        parent.resolve().relative_to(root)
    except ValueError as exc:
        raise PermissionError("adapter target parent resolves outside install root") from exc


def _copy_atomic(source: Path, target: Path, *, root: Path, force: bool) -> None:
    """Publish source without following a pre-created predictable temp symlink."""
    _prepare_parent(root, target.parent, create=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{target.name}.dreamteam-",
        dir=target.parent,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        with source.open("rb") as source_handle:
            shutil.copyfileobj(source_handle, handle)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        _prepare_parent(root, target.parent, create=False)
        if force:
            os.replace(temporary, target)
            return
        try:
            # Hard-link publication is atomic and fails if the target appeared
            # after the earlier existence check. It does not follow target symlinks.
            os.link(temporary, target)
        except FileExistsError as exc:
            raise FileExistsError(f"target appeared during installation: {target}") from exc
        temporary.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()


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
        _copy_atomic(PROJECT_SOURCE, target, root=root, force=force)
    return target


def install_user_skill(
    codex_home: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    home = codex_home.expanduser().resolve()
    target = home / "skills/dreamteam-run/SKILL.md"
    _prepare_parent(home, target.parent, create=False)
    if target.is_symlink():
        raise PermissionError("DreamTeam SKILL.md may not be a symlink")
    if target.exists() and not force:
        raise FileExistsError("DreamTeam Codex skill already exists; use --force to replace it")
    if target.exists() and not target.is_file():
        raise PermissionError("DreamTeam skill target must be a regular file")
    if not dry_run:
        _copy_atomic(SKILL_SOURCE, target, root=home, force=force)
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
