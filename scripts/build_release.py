#!/usr/bin/env python3
"""Build deterministic repository and Claude Code plugin release archives."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"
VERSION = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
EXCLUDE_PARTS = {".git", "dist", "build", "__pycache__", ".pytest_cache", ".dreamteam"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not EXCLUDE_PARTS.intersection(relative.parts) and path.suffix not in EXCLUDE_SUFFIXES


def write_zip(output: Path, archive_root: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files, key=lambda item: item.as_posix()):
            name = path.relative_to(archive_root.parent).as_posix()
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = mode << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    DIST.mkdir(exist_ok=True)
    for child in DIST.iterdir():
        if child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)
    repo_files = [path for path in ROOT.rglob("*") if path.is_file() and included(path)]
    repo_zip = DIST / f"dreamteam-agent-toolkit-{VERSION}.zip"
    write_zip(repo_zip, ROOT, repo_files)
    plugin_files = [path for path in PLUGIN.rglob("*") if path.is_file() and included(path)]
    plugin_zip = DIST / f"dreamteam-claude-code-plugin-{VERSION}.zip"
    write_zip(plugin_zip, PLUGIN, plugin_files)
    checksums = {path.name: sha256(path.read_bytes()).hexdigest() for path in (repo_zip, plugin_zip)}
    (DIST / "SHA256SUMS.json").write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, value in checksums.items():
        print(value, name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
