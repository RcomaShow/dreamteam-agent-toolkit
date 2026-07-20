#!/usr/bin/env python3
"""Build deterministic release archives from the reviewed Git tree only."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"
VERSION = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
EXCLUDE_PARTS = {".git", "dist", "build", "__pycache__", ".pytest_cache", ".dreamteam"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def _git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
    )
    return result.stdout


def require_clean_tree() -> None:
    status = _git("status", "--porcelain=v1", "--untracked-files=all").decode("utf-8")
    if status.strip():
        raise RuntimeError("release build requires a clean Git working tree")


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not EXCLUDE_PARTS.intersection(relative.parts) and path.suffix not in EXCLUDE_SUFFIXES


def tracked_files() -> list[Path]:
    files: list[Path] = []
    for raw in _git("ls-files", "-z").split(b"\0"):
        if not raw:
            continue
        path = ROOT / raw.decode("utf-8")
        if path.is_symlink():
            raise RuntimeError(f"release refuses symlink: {path.relative_to(ROOT)}")
        if path.is_file() and included(path):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def write_zip(
    output: Path,
    *,
    archive_root: Path,
    prefix: str,
    files: list[Path],
) -> dict[str, str]:
    manifest: dict[str, str] = {}
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(archive_root).as_posix()
            name = f"{prefix}/{relative}"
            data = path.read_bytes()
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = mode << 16
            archive.writestr(info, data)
            manifest[relative] = sha256(data).hexdigest()
    return manifest

def main() -> int:
    require_clean_tree()
    DIST.mkdir(exist_ok=True)
    for child in DIST.iterdir():
        if child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)

    files = tracked_files()
    repo_zip = DIST / f"dreamteam-agent-toolkit-{VERSION}.zip"
    repo_manifest = write_zip(
        repo_zip,
        archive_root=ROOT,
        prefix=f"dreamteam-agent-toolkit-{VERSION}",
        files=files,
    )

    plugin_files = [path for path in files if path.is_relative_to(PLUGIN)]
    plugin_zip = DIST / f"dreamteam-claude-code-plugin-{VERSION}.zip"
    plugin_manifest = write_zip(
        plugin_zip,
        archive_root=PLUGIN,
        prefix="dreamteam",
        files=plugin_files,
    )

    commit = _git("rev-parse", "HEAD").decode("utf-8").strip()
    source_manifest = {
        "version": VERSION,
        "commit": commit,
        "repository_files": repo_manifest,
        "plugin_files": plugin_manifest,
    }
    (DIST / "SOURCE_MANIFEST.json").write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksums = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in (repo_zip, plugin_zip, DIST / "SOURCE_MANIFEST.json")
    }
    (DIST / "SHA256SUMS.json").write_text(
        json.dumps(checksums, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for name, value in checksums.items():
        print(value, name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
