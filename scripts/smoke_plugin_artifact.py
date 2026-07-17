#!/usr/bin/env python3
"""Smoke-test the exact plugin ZIP in an isolated directory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {command}\n{result.stdout}\n{result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(args.archive) as archive:
            names = archive.namelist()
            if not names or not all(safe_member(name) for name in names):
                raise ValueError("unsafe or empty plugin archive")
            archive.extractall(root)
        plugin = root / "dreamteam"
        manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        if manifest.get("version") != "0.3.0":
            raise ValueError("unexpected plugin version")
        for required in (
            "lib/dreamteam/config.py", "lib/dreamteam/routing.py", "lib/dreamteam/ledger.py",
            "scripts/dreamteam_route.py", "scripts/dreamteam_measure.py", "scripts/dreamteam_anchor.py",
            "scripts/dreamteam_ledger_hook.py", "hooks/hooks.json",
        ):
            if not (plugin / required).is_file():
                raise FileNotFoundError(required)
        env = os.environ.copy()
        env["PYTHONPATH"] = ""
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin)
        env["CLAUDE_PLUGIN_DATA"] = str(root / "data")
        run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(plugin / 'lib')!r}); import dreamteam; assert dreamteam.__version__ == '0.3.0'"], cwd=root, env=env)
        run([sys.executable, str(plugin / "scripts/dreamteam_measure.py")], cwd=root, env=env)
        run([sys.executable, str(plugin / "scripts/dreamteam_anchor.py"), "--help"], cwd=root, env=env)
        config = root / "config.json"
        config.write_text(json.dumps({
            "version": 2, "topology": "lean", "pricingAsOf": "2026-07-17",
            "verification": {"requireIndependentWriterReview": True, "requireAnchorValidation": True},
            "telemetry": {"storeSourceContent": False, "ledger": "off", "enforcement": "advisory"}
        }), encoding="utf-8")
        request = root / "request.json"
        request.write_text(json.dumps({
            "criticality": "M0", "task_kind": "discovery", "calibration_samples": 20,
            "independent_verifier_available": True,
            "direct_usage": {"input_tokens": 100000, "output_tokens": 2000},
            "worker_usage": {"input_tokens": 100000, "output_tokens": 500},
            "lead_usage": {"input_tokens": 1000, "output_tokens": 200}
        }), encoding="utf-8")
        run([sys.executable, str(plugin / "scripts/dreamteam_route.py"), "--config", str(config), "--request", str(request), "--shadow"], cwd=root, env=env)
        hook_input = json.dumps({"cwd": str(root), "hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {}, "session_id": "smoke"})
        result = subprocess.run([sys.executable, str(plugin / "scripts/dreamteam_ledger_hook.py"), "pre"], cwd=root, env=env, text=True, input=hook_input, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        if any((root / name).exists() for name in (".dreamteam-bootstrap", "scripts/bootstrap_v03.py")):
            raise ValueError("temporary release files found")
        print("plugin artifact smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
