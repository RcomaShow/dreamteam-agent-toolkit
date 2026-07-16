#!/usr/bin/env python3
"""Validate and build repository and Claude plugin ZIP archives."""

from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = json.loads(
    (ROOT / "adapters/claude-code/plugins/dreamteam/.claude-plugin/plugin.json").read_text()
)["version"]

subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], check=True)
DIST.mkdir(exist_ok=True)

def zip_tree(source: Path, destination: Path, prefix: str = "") -> None:
    if destination.exists():
        destination.unlink()
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            if any(part in {".git", "dist", "__pycache__", ".pytest_cache"} for part in path.parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            arc = Path(prefix) / path.relative_to(source)
            zf.write(path, arc.as_posix())

repo_zip = DIST / f"dreamteam-agent-toolkit-{VERSION}.zip"
plugin_zip = DIST / f"dreamteam-claude-code-plugin-{VERSION}.zip"
zip_tree(ROOT, repo_zip, f"dreamteam-agent-toolkit-{VERSION}")
zip_tree(ROOT / "adapters/claude-code/plugins/dreamteam", plugin_zip, "dreamteam")

manifest = {}
for path in sorted(ROOT.rglob("*")):
    if (
        path.is_file()
        and not any(part in {".git", "dist", "__pycache__", ".pytest_cache"} for part in path.parts)
        and path.suffix not in {".pyc", ".pyo"}
    ):
        manifest[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
(DIST / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(repo_zip)
print(plugin_zip)
