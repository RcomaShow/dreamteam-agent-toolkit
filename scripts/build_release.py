#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = json.loads((ROOT / "adapters/claude-code/plugins/dreamteam/.claude-plugin/plugin.json").read_text())["version"]

EXCLUDE_PARTS = {".git", "dist", "build", "__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return not EXCLUDE_PARTS.intersection(rel.parts) and path.suffix not in EXCLUDE_SUFFIXES


def write_zip(output: Path, base: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(base.parent))


DIST.mkdir(exist_ok=True)
for child in DIST.iterdir():
    if child.is_file(): child.unlink()
    elif child.is_dir(): shutil.rmtree(child)

repo_files = [path for path in ROOT.rglob("*") if path.is_file() and included(path)]
repo_zip = DIST / f"dreamteam-agent-toolkit-{VERSION}.zip"
write_zip(repo_zip, ROOT, repo_files)

plugin = ROOT / "adapters/claude-code/plugins/dreamteam"
plugin_files = [path for path in plugin.rglob("*") if path.is_file() and included(path)]
plugin_zip = DIST / f"dreamteam-claude-code-plugin-{VERSION}.zip"
write_zip(plugin_zip, plugin, plugin_files)

checksums = {}
for path in (repo_zip, plugin_zip):
    checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(DIST / "SHA256SUMS.json").write_text(json.dumps(checksums, indent=2) + "\n")
for name, value in checksums.items(): print(value, name)
