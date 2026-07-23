#!/usr/bin/env python3
"""Install and manage the DreamTeam standalone Claude Code adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

HERE = Path(__file__).resolve().parent
LIB = HERE / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from dreamteam_standalone import (  # noqa: E402
    DoctorReport,
    InstallResult,
    StandaloneInstallError,
    doctor,
    install as _install,
    uninstall,
)


def install(
    *,
    scope: str,
    project_root: str | Path | None = None,
    home: str | Path | None = None,
    source_plugin_root: str | Path | None = None,
    enable_hooks: bool = False,
    force: bool = False,
    dry_run: bool = False,
    python_command: str | None = None,
) -> InstallResult:
    """Compatibility facade using the public CLI argument name."""
    return _install(
        scope=scope,
        project_root=project_root,
        home=home,
        source_plugin_root_path=source_plugin_root,
        enable_hooks=enable_hooks,
        force=force,
        dry_run=dry_run,
        python_command=python_command,
    )


def render_result(result: InstallResult) -> str:
    return "\n".join(
        (
            f"DREAMTEAM_STANDALONE|{result.action.upper()}",
            f"SCOPE|{result.scope}",
            f"CLAUDE_ROOT|{result.claude_root}",
            f"RUNTIME_ROOT|{result.runtime_root}",
            f"FILES|{result.files}",
            f"HOOKS|{'enabled' if result.hooks_enabled else 'disabled'}",
            f"DRY_RUN|{str(result.dry_run).lower()}",
        )
    )


def render_doctor(report: DoctorReport) -> str:
    lines = [
        "DREAMTEAM_STANDALONE_DOCTOR|1",
        f"STATUS|{'READY' if report.ready else 'BLOCKED'}",
        f"SCOPE|{report.scope or ''}",
        f"CLAUDE_ROOT|{report.claude_root}",
        f"RUNTIME_ROOT|{report.runtime_root}",
        f"ADAPTER_VERSION|{report.adapter_version or ''}",
        f"HOOKS|{'' if report.hooks_enabled is None else str(report.hooks_enabled).lower()}",
    ]
    for diagnostic in report.diagnostics:
        prefix = "CHECK" if diagnostic.severity == "info" else "ISSUE"
        lines.append(
            f"{prefix}|{diagnostic.severity.upper()}|"
            f"{diagnostic.code}|{diagnostic.message}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            result = install(
                scope=args.scope,
                project_root=args.project_root,
                source_plugin_root=args.source_plugin_root,
                enable_hooks=args.enable_hooks,
                force=args.force,
                dry_run=args.dry_run,
                python_command=args.python_command,
            )
            _emit(result.payload(), render_result(result), args.format)
            return 0
        if args.command == "doctor":
            report = doctor(scope=args.scope, project_root=args.project_root)
            _emit(report.payload(), render_doctor(report), args.format)
            return 0 if report.ready else 1
        if args.command == "uninstall":
            result = uninstall(
                scope=args.scope,
                project_root=args.project_root,
                force=args.force,
                dry_run=args.dry_run,
            )
            _emit(result.payload(), render_result(result), args.format)
            return 0
        parser.error("a command is required")
    except (OSError, TypeError, ValueError, StandaloneInstallError) as exc:
        parser.exit(2, f"ERROR|{type(exc).__name__}|{exc}\n")
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="install_claude_standalone",
        description="Install, inspect, or remove the DreamTeam standalone Claude Code adapter.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="install or upgrade the adapter")
    _target_arguments(install_parser)
    install_parser.add_argument("--source-plugin-root")
    install_parser.add_argument("--enable-hooks", action="store_true")
    install_parser.add_argument("--python-command")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--format", choices=("text", "json"), default="text")

    doctor_parser = subparsers.add_parser("doctor", help="inspect an installation")
    _target_arguments(doctor_parser)
    doctor_parser.add_argument("--format", choices=("text", "json"), default="text")

    uninstall_parser = subparsers.add_parser("uninstall", help="remove a tracked installation")
    _target_arguments(uninstall_parser)
    uninstall_parser.add_argument("--force", action="store_true")
    uninstall_parser.add_argument("--dry-run", action="store_true")
    uninstall_parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _target_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--project-root", default=".")


def _emit(payload: Mapping[str, object], text: str, format_name: str) -> None:
    if format_name == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(text)


if __name__ == "__main__":
    raise SystemExit(main())
