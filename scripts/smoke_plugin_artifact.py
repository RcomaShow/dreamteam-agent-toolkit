#!/usr/bin/env python3
"""Smoke-test the exact DreamTeam 0.4.1 plugin ZIP in an isolated directory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

EXPECTED_VERSION = "0.4.1"


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        input=input_text,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed: {command}\n{result.stdout}\n{result.stderr}"
        )
    return result


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
        manifest = json.loads(
            (plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
        )
        if manifest.get("version") != EXPECTED_VERSION:
            raise ValueError("unexpected plugin version")
        for required in (
            "lib/dreamteam/config.py",
            "lib/dreamteam/routing.py",
            "lib/dreamteam/ledger.py",
            "lib/dreamteam/protocol.py",
            "lib/dreamteam/operations.py",
            "lib/dreamteam/py.typed",
            "scripts/dreamteam_init.py",
            "scripts/dreamteam_route.py",
            "scripts/dreamteam_measure.py",
            "scripts/dreamteam_anchor.py",
            "scripts/dreamteam_protocol.py",
            "scripts/dreamteam_ledger_hook.py",
            "hooks/hooks.json",
            "skills/init/SKILL.md",
            "skills/doctor/SKILL.md",
            "skills/status/SKILL.md",
            "agents/execution-sonnet-lead.md",
            "agents/verification-independent-reviewer.md",
        ):
            if not (plugin / required).is_file():
                raise FileNotFoundError(required)

        env = os.environ.copy()
        env["PYTHONPATH"] = ""
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin)
        env["CLAUDE_PLUGIN_DATA"] = str(root / "data")
        run(
            [
                sys.executable,
                "-I",
                "-c",
                (
                    f"import sys; sys.path.insert(0, {str(plugin / 'lib')!r}); "
                    "import dreamteam; import dreamteam.operations; "
                    f"assert dreamteam.__version__ == {EXPECTED_VERSION!r}"
                ),
            ],
            cwd=root,
            env=env,
        )
        run(
            [sys.executable, str(plugin / "scripts/dreamteam_measure.py")],
            cwd=root,
            env=env,
        )
        run(
            [sys.executable, str(plugin / "scripts/dreamteam_anchor.py"), "--help"],
            cwd=root,
            env=env,
        )
        run(
            [sys.executable, str(plugin / "scripts/dreamteam_protocol.py"), "--help"],
            cwd=root,
            env=env,
        )

        project = root / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        initialized = run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_init.py"),
                "--project-root",
                str(project),
                "--format",
                "json",
            ],
            cwd=project,
            env=env,
        )
        init_payload = json.loads(initialized.stdout)
        if init_payload["topology"] != "lean" or init_payload["enforcement"] != "advisory":
            raise ValueError("init did not create the recommended advisory defaults")
        project_config = project / "dreamteam.config.json"
        if not project_config.is_file():
            raise FileNotFoundError("dreamteam.config.json")

        diagnosed = run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_route.py"),
                "doctor",
                "--project-root",
                str(project),
                "--plugin-root",
                str(plugin),
                "--hooks-available",
                "--format",
                "json",
            ],
            cwd=project,
            env=env,
        )
        if json.loads(diagnosed.stdout)["ready"] is not True:
            raise ValueError("doctor did not accept the initialized plugin project")

        config = root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "version": 2,
                    "topology": "opus-sonnet",
                    "profile": "balanced",
                    "pricingAsOf": "2026-07-17",
                    "verification": {
                        "requireIndependentWriterReview": True,
                        "requireAnchorValidation": True,
                    },
                    "telemetry": {
                        "enabled": False,
                        "storeSourceContent": False,
                        "ledger": "off",
                        "enforcement": "advisory",
                    },
                }
            ),
            encoding="utf-8",
        )
        request = root / "request.json"
        request.write_text(
            json.dumps(
                {
                    "criticality": "L2",
                    "task_kind": "review",
                    "calibration_samples": 20,
                    "independent_verifier_available": True,
                    "direct_usage": {
                        "input_tokens": 1_000_000,
                        "output_tokens": 100_000,
                    },
                    "lead_usage": {"input_tokens": 50_000, "output_tokens": 2_000},
                    "executive_usage": {
                        "input_tokens": 10_000,
                        "output_tokens": 1_000,
                    },
                }
            ),
            encoding="utf-8",
        )
        routed = run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_route.py"),
                "--config",
                str(config),
                "--request",
                str(request),
                "--shadow",
            ],
            cwd=root,
            env=env,
        )
        payload = json.loads(routed.stdout)
        if payload["selected_agent_role"] != "verification-independent-reviewer":
            raise ValueError("Opus-Sonnet smoke route did not select the Sonnet reviewer")

        (project / "a.py").write_text("a\n", encoding="utf-8")
        strict = json.loads(config.read_text(encoding="utf-8"))
        strict["topology"] = "lean"
        strict["telemetry"] = {
            "enabled": True,
            "storeSourceContent": False,
            "ledger": "sqlite",
            "enforcement": "strict",
        }
        project_config.write_text(json.dumps(strict), encoding="utf-8")
        hook_env = env | {
            "CLAUDE_PROJECT_DIR": str(project),
            "DREAMTEAM_RUN_ID": "smoke",
            "DREAMTEAM_NEXT_AGENT_USD_MICROS": "100",
        }
        event = json.dumps(
            {
                "cwd": str(project),
                "hook_event_name": "PreToolUse",
                "tool_name": "Agent",
                "tool_use_id": "tool-smoke",
                "tool_input": {"description": "worker"},
                "session_id": "smoke",
            }
        )
        run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_ledger_hook.py"),
                "pre",
            ],
            cwd=project,
            env=hook_env,
            input_text=event,
        )
        post_event = json.dumps(
            {
                "cwd": str(project),
                "hook_event_name": "PostToolUse",
                "tool_name": "Agent",
                "tool_use_id": "tool-smoke",
                "tool_input": {"description": "worker"},
                "session_id": "smoke",
            }
        )
        run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_ledger_hook.py"),
                "post",
            ],
            cwd=project,
            env=hook_env,
            input_text=post_event,
        )
        database = Path(hook_env["CLAUDE_PLUGIN_DATA"]) / "ledger.sqlite"
        with sqlite3.connect(database) as connection:
            charged = connection.execute(
                "SELECT COALESCE(SUM(usd_micros),0) FROM charges WHERE run_id='smoke'"
            ).fetchone()[0]
        if charged != 100:
            raise ValueError("hook did not commit the Agent reservation")

        reported = run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_route.py"),
                "status",
                "--project-root",
                str(project),
                "--plugin-data",
                str(Path(hook_env["CLAUDE_PLUGIN_DATA"])),
                "--run",
                "smoke",
                "--format",
                "json",
            ],
            cwd=project,
            env=hook_env,
        )
        status_payload = json.loads(reported.stdout)
        if status_payload["charged_usd_micros"] != 100:
            raise ValueError("status did not report the committed charge")
        if status_payload["reserved_usd_micros"] != 0:
            raise ValueError("status reported a stale active reservation")

        contract_file = project / "smoke.dcp2"
        contract_file.write_text(
            "\n".join(
                [
                    "DCP|2",
                    "RUN|smoke",
                    "TASK|smoke-task",
                    "CONST|DT-C1",
                    "PROFILE|balanced",
                    "G|validate installed handoff",
                    "S+|a.py",
                    "T|inspect",
                    "B|files=1;deep_reads=1;turns=2;records=10;retries=0",
                    "O|CHP/2",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        bound = run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_protocol.py"),
                str(contract_file),
                "--hash",
                "--bind",
                "--ledger",
                str(database),
            ],
            cwd=project,
            env=hook_env,
        )
        contract_hash = next(
            line for line in bound.stdout.splitlines() if line.startswith("sha256:")
        )
        handoff = "\n".join(
            [
                "CHP|2",
                "RUN|smoke",
                "TASK|smoke-task",
                f"CONTRACT|{contract_hash}",
                "S|DONE|installed runtime accepted the bounded handoff",
                "N|ORCHESTRATOR|accept",
                "",
            ]
        )
        stop_event = json.dumps(
            {
                "cwd": str(project),
                "hook_event_name": "SubagentStop",
                "agent_id": "smoke-agent",
                "agent_type": "discovery-symbol-locator",
                "last_assistant_message": handoff,
                "stop_hook_active": False,
                "session_id": "smoke",
            }
        )
        run(
            [
                sys.executable,
                str(plugin / "scripts/dreamteam_ledger_hook.py"),
                "subagent-stop",
            ],
            cwd=project,
            env=hook_env,
            input_text=stop_event,
        )
        with sqlite3.connect(database) as connection:
            state = connection.execute(
                "SELECT state FROM checkpoints WHERE run_id='smoke' AND node_id='smoke-agent'"
            ).fetchone()
        if state != ("DONE",):
            raise ValueError("installed plugin did not validate the bound CHP/2 handoff")

        if any(
            (root / name).exists()
            for name in (".dreamteam-bootstrap", ".dreamteam-tree-probe")
        ):
            raise ValueError("temporary release files found")
        print("plugin artifact smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
