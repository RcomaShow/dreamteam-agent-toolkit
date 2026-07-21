"""Deterministic onboarding, diagnostics, and metadata-only run status."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any, Sequence, TextIO

from . import __version__
from .config import Profile, RuntimeConfig, Topology

CONFIG_FILENAME = "dreamteam.config.json"
DEFAULT_PRICING_AS_OF = date(2026, 7, 17)
REPORT_SCHEMA_VERSION = 1
_DIAGNOSTIC_SEVERITIES = {"info", "warning", "error"}


@dataclass(frozen=True)
class InitResult:
    path: str
    replaced: bool
    topology: str
    profile: str
    pricing_as_of: str
    telemetry_enabled: bool
    ledger: str
    enforcement: str


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    fix: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in _DIAGNOSTIC_SEVERITIES:
            raise ValueError(f"unsupported diagnostic severity: {self.severity}")
        if not self.code or not self.message:
            raise ValueError("diagnostic code and message are required")


@dataclass(frozen=True)
class DoctorReport:
    schema_version: int
    toolkit_version: str
    ready: bool
    project_root: str
    config_path: str
    config_hash: str | None
    topology: str | None
    profile: str | None
    pricing_as_of: str | None
    telemetry_enabled: bool | None
    ledger: str | None
    enforcement: str | None
    diagnostics: tuple[Diagnostic, ...]

    def payload(self) -> dict[str, object]:
        data = asdict(self)
        data["diagnostics"] = [asdict(item) for item in self.diagnostics]
        return data


@dataclass(frozen=True)
class StatusReport:
    schema_version: int
    toolkit_version: str
    available: bool
    project_root: str
    ledger_path: str | None
    run_id: str | None
    config_hash: str | None
    charged_usd_micros: int
    reserved_usd_micros: int
    active_workers: int
    checkpoint_counts: dict[str, int]
    failed_tool_events: int
    invalidation_categories: tuple[str, ...]
    reason_code: str | None = None
    message: str | None = None
    fix: str | None = None

    def payload(self) -> dict[str, object]:
        data = asdict(self)
        data["invalidation_categories"] = list(self.invalidation_categories)
        return data


def minimal_config(
    *,
    topology: Topology | str = Topology.LEAN,
    profile: Profile | str = Profile.BALANCED,
    strict: bool = False,
    pricing_as_of: date = DEFAULT_PRICING_AS_OF,
) -> dict[str, object]:
    """Return the smallest complete config accepted by the strict parser."""
    if not isinstance(topology, Topology):
        topology = Topology(topology)
    if not isinstance(profile, Profile):
        profile = Profile(profile)
    if type(strict) is not bool:
        raise TypeError("strict must be a boolean")
    if not isinstance(pricing_as_of, date):
        raise TypeError("pricing_as_of must be a date")

    telemetry: dict[str, object]
    if strict:
        telemetry = {
            "enabled": True,
            "storeSourceContent": False,
            "ledger": "sqlite",
            "enforcement": "strict",
        }
    else:
        telemetry = {
            "enabled": False,
            "storeSourceContent": False,
            "ledger": "off",
            "enforcement": "advisory",
        }

    data: dict[str, object] = {
        "version": 2,
        "constitution": "DT-C1",
        "topology": topology.value,
        "profile": profile.value,
        "pricingAsOf": pricing_as_of.isoformat(),
        "models": {
            "executive": "inherit",
            "lead": "sonnet",
            "workers": "haiku",
        },
        "routing": {
            "maxEscalationProbability": 0.25,
            "maxMainRereadRatio": 0.35,
            "minSamplesForEnforcement": 20,
            "allowClosedContextBatch": False,
        },
        "budgets": {"maxRunUsd": 1.0},
        "verification": {
            "requireIndependentWriterReview": True,
            "requireAnchorValidation": True,
            "allowFullSuite": "orchestrator-only",
        },
        "telemetry": telemetry,
    }
    RuntimeConfig.from_mapping(data)
    return data


def write_minimal_config(
    project_root: str | Path,
    *,
    topology: Topology | str = Topology.LEAN,
    profile: Profile | str = Profile.BALANCED,
    strict: bool = False,
    force: bool = False,
    pricing_as_of: date = DEFAULT_PRICING_AS_OF,
) -> InitResult:
    """Write ``dreamteam.config.json`` atomically without following a target symlink."""
    if type(force) is not bool:
        raise TypeError("force must be a boolean")
    root = _project_root(project_root)
    target = root / CONFIG_FILENAME
    if target.is_symlink():
        raise PermissionError(f"{CONFIG_FILENAME} may not be a symlink")
    replaced = target.exists()
    if replaced and not target.is_file():
        raise PermissionError(f"{CONFIG_FILENAME} must be a regular file")
    if replaced and not force:
        raise FileExistsError(f"{CONFIG_FILENAME} already exists; pass --force to replace it")

    data = minimal_config(
        topology=topology,
        profile=profile,
        strict=strict,
        pricing_as_of=pricing_as_of,
    )
    serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=root,
            prefix=f".{CONFIG_FILENAME}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
            temporary = Path(stream.name)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    parsed = RuntimeConfig.from_mapping(data)
    return InitResult(
        path=str(target),
        replaced=replaced,
        topology=parsed.topology.value,
        profile=parsed.profile.value,
        pricing_as_of=parsed.pricing_as_of.isoformat(),
        telemetry_enabled=parsed.telemetry.enabled,
        ledger=parsed.telemetry.ledger,
        enforcement=parsed.telemetry.enforcement,
    )


def doctor(
    project_root: str | Path,
    *,
    plugin_root: str | Path | None = None,
    plugin_data: str | Path | None = None,
    hooks_available: bool | None = None,
) -> DoctorReport:
    """Inspect configuration and runtime readiness without modifying project state."""
    root = _project_root(project_root)
    config_path = root / CONFIG_FILENAME
    diagnostics: list[Diagnostic] = []
    config_hash: str | None = None
    config: RuntimeConfig | None = None

    if config_path.is_symlink():
        diagnostics.append(
            Diagnostic(
                "error",
                "CONFIG_SYMLINK",
                f"{CONFIG_FILENAME} is a symlink and will be rejected by enforcement hooks.",
                f"Replace it with a regular project-root file: /dreamteam:init --force",
            )
        )
    elif not config_path.exists():
        diagnostics.append(
            Diagnostic(
                "error",
                "CONFIG_MISSING",
                f"{CONFIG_FILENAME} was not found in the project root.",
                "Run /dreamteam:init",
            )
        )
    elif not config_path.is_file():
        diagnostics.append(
            Diagnostic(
                "error",
                "CONFIG_NOT_FILE",
                f"{CONFIG_FILENAME} is not a regular file.",
                f"Replace it with a regular file generated by /dreamteam:init --force",
            )
        )
    else:
        try:
            raw = config_path.read_bytes()
            config_hash = sha256(raw).hexdigest()
            decoded = raw.decode("utf-8")
            data = json.loads(decoded)
            if not isinstance(data, dict):
                raise TypeError("configuration root must be an object")
            config = RuntimeConfig.from_mapping(data)
            diagnostics.append(
                Diagnostic(
                    "info",
                    "CONFIG_VALID",
                    "The project configuration passes strict schema validation.",
                )
            )
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "CONFIG_INVALID",
                    f"The project configuration is invalid: {exc}",
                    "Repair the reported field or regenerate with /dreamteam:init --force",
                )
            )

    resolved_plugin_root: Path | None = None
    if plugin_root is not None:
        candidate = Path(plugin_root).expanduser()
        if candidate.exists():
            resolved_plugin_root = candidate.resolve(strict=True)
            _check_plugin(resolved_plugin_root, diagnostics)
        else:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "PLUGIN_ROOT_MISSING",
                    f"Plugin root does not exist: {candidate}",
                    "Reinstall the DreamTeam plugin and run /dreamteam:doctor again.",
                )
            )
    else:
        diagnostics.append(
            Diagnostic(
                "warning",
                "PLUGIN_ROOT_UNKNOWN",
                "Plugin packaging was not inspected because no plugin root was supplied.",
                "Run /dreamteam:doctor from the installed Claude Code plugin.",
            )
        )

    if hooks_available is None and resolved_plugin_root is not None:
        hooks_available = (resolved_plugin_root / "hooks/hooks.json").is_file()

    if config is not None:
        if config.topology is Topology.OPUS_SONNET:
            diagnostics.append(
                Diagnostic(
                    "info",
                    "OPUS_SONNET_ROLES_DISTINCT",
                    "Opus owns executive decisions; the Sonnet bounded implementer and independent reviewer are distinct agent identities.",
                )
            )
        if config.budgets.max_run_usd == 0:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "ZERO_RUN_BUDGET",
                    "maxRunUsd is zero, so every non-zero-cost route will be blocked.",
                    "Set budgets.maxRunUsd to a positive reviewed limit.",
                )
            )
        if not config.telemetry.enabled:
            diagnostics.append(
                Diagnostic(
                    "info",
                    "ADVISORY_DEFAULT",
                    "Telemetry is disabled and enforcement is advisory; this is the recommended first-run mode.",
                )
            )
        else:
            data_root = _plugin_data_root(root, plugin_data)
            _check_ledger_location(data_root, diagnostics)
            if config.telemetry.enforcement == "strict" and hooks_available is not True:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "STRICT_HOOKS_REQUIRED",
                        "Strict enforcement is configured but hook availability was not confirmed.",
                        "Run through the installed Claude Code plugin or pass --hooks-available after verifying hooks.json.",
                    )
                )

    ready = not any(item.severity == "error" for item in diagnostics)
    return DoctorReport(
        schema_version=REPORT_SCHEMA_VERSION,
        toolkit_version=__version__,
        ready=ready,
        project_root=str(root),
        config_path=str(config_path),
        config_hash=config_hash,
        topology=None if config is None else config.topology.value,
        profile=None if config is None else config.profile.value,
        pricing_as_of=None if config is None else config.pricing_as_of.isoformat(),
        telemetry_enabled=None if config is None else config.telemetry.enabled,
        ledger=None if config is None else config.telemetry.ledger,
        enforcement=None if config is None else config.telemetry.enforcement,
        diagnostics=tuple(diagnostics),
    )


def status(
    project_root: str | Path,
    *,
    plugin_data: str | Path | None = None,
    run_id: str | None = None,
) -> StatusReport:
    """Read a redacted status summary from the metadata-only SQLite ledger."""
    root = _project_root(project_root)
    config_path = root / CONFIG_FILENAME
    if not config_path.is_file() or config_path.is_symlink():
        return _unavailable_status(
            root,
            None,
            "CONFIG_UNAVAILABLE",
            f"A regular {CONFIG_FILENAME} is required before status can be read.",
            "Run /dreamteam:init and /dreamteam:doctor.",
        )
    try:
        config = RuntimeConfig.from_file(config_path)
    except (OSError, TypeError, ValueError) as exc:
        return _unavailable_status(
            root,
            None,
            "CONFIG_INVALID",
            f"Status cannot load the project configuration: {exc}",
            "Repair the configuration and run /dreamteam:doctor.",
        )
    if not config.telemetry.enabled:
        return _unavailable_status(
            root,
            None,
            "TELEMETRY_DISABLED",
            "No durable run status is retained while telemetry is disabled.",
            "Enable telemetry with ledger=sqlite only after reviewing strict-mode requirements.",
        )

    data_root = _plugin_data_root(root, plugin_data)
    ledger_path = data_root / "ledger.sqlite"
    if ledger_path.is_symlink() or not ledger_path.is_file():
        return _unavailable_status(
            root,
            ledger_path,
            "LEDGER_MISSING",
            "The SQLite ledger does not exist as a regular file.",
            "Run a telemetry-enabled DreamTeam task, then retry /dreamteam:status.",
        )

    try:
        connection = sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True, timeout=5)
        try:
            selected_run, selection_error = _select_run_id(connection, run_id)
            if selection_error is not None:
                code, message, fix = selection_error
                return _unavailable_status(root, ledger_path, code, message, fix)
            assert selected_run is not None
            config_hash_row = connection.execute(
                "SELECT config_hash FROM run_metadata WHERE run_id=?", (selected_run,)
            ).fetchone()
            charged = _scalar(
                connection,
                "SELECT COALESCE(SUM(usd_micros),0) FROM charges WHERE run_id=?",
                selected_run,
            )
            reserved = _scalar(
                connection,
                "SELECT COALESCE(SUM(usd_micros),0) FROM reservations WHERE run_id=?",
                selected_run,
            )
            active_workers = _scalar(
                connection,
                "SELECT COUNT(*) FROM checkpoints WHERE run_id=? AND state IN ('PENDING','RUNNING')",
                selected_run,
            )
            checkpoint_counts = {
                str(state): int(count)
                for state, count in connection.execute(
                    "SELECT state,COUNT(*) FROM checkpoints WHERE run_id=? GROUP BY state ORDER BY state",
                    (selected_run,),
                ).fetchall()
            }
            failed_events = _scalar(
                connection,
                "SELECT COUNT(*) FROM tool_events_v04 WHERE run_id=? AND status='failed'",
                selected_run,
            )
            categories = tuple(
                str(row[0])
                for row in connection.execute(
                    "SELECT DISTINCT category FROM invalidations WHERE run_id=? ORDER BY category",
                    (selected_run,),
                ).fetchall()
            )
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return _unavailable_status(
            root,
            ledger_path,
            "LEDGER_UNREADABLE",
            f"The SQLite ledger could not be read: {exc}",
            "Run /dreamteam:doctor and replace a corrupt ledger only after preserving it for audit.",
        )

    return StatusReport(
        schema_version=REPORT_SCHEMA_VERSION,
        toolkit_version=__version__,
        available=True,
        project_root=str(root),
        ledger_path=str(ledger_path),
        run_id=selected_run,
        config_hash=None if config_hash_row is None else str(config_hash_row[0]),
        charged_usd_micros=charged,
        reserved_usd_micros=reserved,
        active_workers=active_workers,
        checkpoint_counts=checkpoint_counts,
        failed_tool_events=failed_events,
        invalidation_categories=categories,
    )


def render_init_text(result: InitResult) -> str:
    action = "REPLACED" if result.replaced else "CREATED"
    return "\n".join(
        (
            f"CONFIG_{action}|{result.path}",
            f"TOPOLOGY|{result.topology}",
            f"PROFILE|{result.profile}",
            f"PRICING_AS_OF|{result.pricing_as_of}",
            f"TELEMETRY|{'enabled' if result.telemetry_enabled else 'disabled'}",
            f"LEDGER|{result.ledger}",
            f"ENFORCEMENT|{result.enforcement}",
            "NEXT|/dreamteam:doctor",
        )
    )


def render_doctor_text(report: DoctorReport) -> str:
    lines = [
        f"DREAMTEAM_DOCTOR|{report.toolkit_version}",
        f"STATUS|{'READY' if report.ready else 'BLOCKED'}",
        f"PROJECT_ROOT|{report.project_root}",
        f"CONFIG_PATH|{report.config_path}",
        f"CONFIG_HASH|{report.config_hash or ''}",
        f"TOPOLOGY|{report.topology or ''}",
        f"PROFILE|{report.profile or ''}",
        f"PRICING_AS_OF|{report.pricing_as_of or ''}",
        f"TELEMETRY|{'' if report.telemetry_enabled is None else str(report.telemetry_enabled).lower()}",
        f"LEDGER|{report.ledger or ''}",
        f"ENFORCEMENT|{report.enforcement or ''}",
    ]
    for item in report.diagnostics:
        prefix = "CHECK" if item.severity == "info" else "ISSUE"
        lines.append(f"{prefix}|{item.severity.upper()}|{item.code}|{item.message}")
        if item.fix:
            lines.append(f"FIX|{item.code}|{item.fix}")
    return "\n".join(lines)


def render_status_text(report: StatusReport) -> str:
    lines = [
        f"DREAMTEAM_STATUS|{report.toolkit_version}",
        f"STATUS|{'AVAILABLE' if report.available else 'UNAVAILABLE'}",
        f"PROJECT_ROOT|{report.project_root}",
        f"LEDGER_PATH|{report.ledger_path or ''}",
    ]
    if not report.available:
        lines.extend(
            (
                f"REASON|{report.reason_code or ''}|{report.message or ''}",
                f"FIX|{report.reason_code or ''}|{report.fix or ''}",
            )
        )
        return "\n".join(lines)
    lines.extend(
        (
            f"RUN|{report.run_id}",
            f"CONFIG_HASH|{report.config_hash or ''}",
            f"CHARGED_USD_MICROS|{report.charged_usd_micros}",
            f"RESERVED_USD_MICROS|{report.reserved_usd_micros}",
            f"ACTIVE_WORKERS|{report.active_workers}",
            "CHECKPOINTS|"
            + ";".join(f"{key}={value}" for key, value in sorted(report.checkpoint_counts.items())),
            f"FAILED_TOOL_EVENTS|{report.failed_tool_events}",
            "INVALIDATIONS|" + ";".join(report.invalidation_categories),
        )
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = write_minimal_config(
                args.project_root,
                topology=args.topology,
                profile=args.profile,
                strict=args.strict,
                force=args.force,
                pricing_as_of=date.fromisoformat(args.pricing_as_of),
            )
            _emit(asdict(result), render_init_text(result), args.format)
            return 0
        if args.command == "doctor":
            report = doctor(
                args.project_root,
                plugin_root=args.plugin_root,
                plugin_data=args.plugin_data,
                hooks_available=args.hooks_available,
            )
            _emit(report.payload(), render_doctor_text(report), args.format)
            return 0 if report.ready else 1
        if args.command == "status":
            report = status(
                args.project_root,
                plugin_data=args.plugin_data,
                run_id=args.run_id,
            )
            _emit(report.payload(), render_status_text(report), args.format)
            return 0 if report.available else 1
        parser.error("a command is required")
    except (OSError, TypeError, ValueError) as exc:
        parser.exit(2, f"ERROR|{type(exc).__name__}|{exc}\n")
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dreamteam")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a minimal project configuration")
    _project_argument(init_parser)
    init_parser.add_argument("--topology", choices=[item.value for item in Topology], default="lean")
    init_parser.add_argument("--profile", choices=[item.value for item in Profile], default="balanced")
    init_parser.add_argument("--strict", action="store_true")
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--pricing-as-of", default=DEFAULT_PRICING_AS_OF.isoformat())
    _format_argument(init_parser)

    doctor_parser = subparsers.add_parser("doctor", help="inspect project and plugin readiness")
    _project_argument(doctor_parser)
    doctor_parser.add_argument("--plugin-root", type=Path)
    doctor_parser.add_argument("--plugin-data", type=Path)
    doctor_parser.add_argument("--hooks-available", action="store_true", default=None)
    _format_argument(doctor_parser)

    status_parser = subparsers.add_parser("status", help="read metadata-only run status")
    _project_argument(status_parser)
    status_parser.add_argument("--plugin-data", type=Path)
    status_parser.add_argument("--run", dest="run_id")
    _format_argument(status_parser)
    return parser


def _project_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", type=Path, default=Path.cwd())


def _format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("text", "json"), default="text")


def _emit(payload: dict[str, object], text: str, output_format: str, stream: TextIO | None = None) -> None:
    target = stream if stream is not None else sys.stdout
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True), file=target)
    else:
        print(text, file=target)


def _project_root(project_root: str | Path) -> Path:
    root = Path(project_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"project root is not a directory: {root}")
    return root


def _plugin_data_root(project_root: Path, plugin_data: str | Path | None) -> Path:
    raw = plugin_data if plugin_data is not None else os.environ.get("CLAUDE_PLUGIN_DATA")
    return (project_root / ".dreamteam") if raw is None else Path(raw).expanduser()


def _check_plugin(plugin_root: Path, diagnostics: list[Diagnostic]) -> None:
    manifest_path = plugin_root / ".claude-plugin/plugin.json"
    hooks_path = plugin_root / "hooks/hooks.json"
    route_path = plugin_root / "scripts/dreamteam_route.py"
    if not manifest_path.is_file():
        diagnostics.append(
            Diagnostic(
                "error",
                "PLUGIN_MANIFEST_MISSING",
                "The plugin manifest is missing.",
                "Reinstall DreamTeam from the marketplace.",
            )
        )
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            version = manifest.get("version") if isinstance(manifest, dict) else None
            if version != __version__:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "PLUGIN_VERSION_MISMATCH",
                        f"Plugin version {version!r} does not match runtime {__version__}.",
                        "Reinstall or regenerate the plugin adapter.",
                    )
                )
            else:
                diagnostics.append(
                    Diagnostic("info", "PLUGIN_VERSION_VALID", f"Plugin version {version} is coherent.")
                )
        except (OSError, json.JSONDecodeError) as exc:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "PLUGIN_MANIFEST_INVALID",
                    f"The plugin manifest is invalid: {exc}",
                    "Reinstall or regenerate the plugin adapter.",
                )
            )
    for code, path, label in (
        ("HOOKS_MISSING", hooks_path, "hooks.json"),
        ("ROUTE_WRAPPER_MISSING", route_path, "dreamteam_route.py"),
    ):
        if not path.is_file():
            diagnostics.append(
                Diagnostic(
                    "error",
                    code,
                    f"The installed plugin is missing {label}.",
                    "Reinstall or regenerate the plugin adapter.",
                )
            )
    agents = list((plugin_root / "agents").glob("*.md"))
    if len(agents) != 16:
        diagnostics.append(
            Diagnostic(
                "error",
                "AGENT_CATALOG_INCOMPLETE",
                f"Expected 16 generated agents, found {len(agents)}.",
                "Run scripts/sync_claude_adapter.py and reinstall the artifact.",
            )
        )
    else:
        diagnostics.append(
            Diagnostic("info", "AGENT_CATALOG_VALID", "The generated catalog contains 16 agents.")
        )


def _check_ledger_location(data_root: Path, diagnostics: list[Diagnostic]) -> None:
    if data_root.is_symlink():
        diagnostics.append(
            Diagnostic(
                "error",
                "PLUGIN_DATA_SYMLINK",
                "Claude plugin data resolves through a symlink.",
                "Use a regular private directory for CLAUDE_PLUGIN_DATA.",
            )
        )
        return
    if data_root.exists() and not data_root.is_dir():
        diagnostics.append(
            Diagnostic(
                "error",
                "PLUGIN_DATA_NOT_DIRECTORY",
                f"Plugin data path is not a directory: {data_root}",
                "Set CLAUDE_PLUGIN_DATA to a writable directory.",
            )
        )
        return
    parent = data_root if data_root.exists() else data_root.parent
    if not parent.exists() or not os.access(parent, os.W_OK):
        diagnostics.append(
            Diagnostic(
                "error",
                "PLUGIN_DATA_NOT_WRITABLE",
                f"Plugin data cannot be created or written at {data_root}.",
                "Choose a writable CLAUDE_PLUGIN_DATA directory.",
            )
        )
        return
    ledger_path = data_root / "ledger.sqlite"
    if ledger_path.is_symlink():
        diagnostics.append(
            Diagnostic(
                "error",
                "LEDGER_SYMLINK",
                "The SQLite ledger may not be a symlink.",
                "Move the ledger to a regular file inside Claude plugin data.",
            )
        )
    elif ledger_path.exists() and not ledger_path.is_file():
        diagnostics.append(
            Diagnostic(
                "error",
                "LEDGER_NOT_FILE",
                "The SQLite ledger path is not a regular file.",
                "Replace it with a regular SQLite file.",
            )
        )
    elif not ledger_path.exists():
        diagnostics.append(
            Diagnostic(
                "warning",
                "LEDGER_NOT_CREATED",
                "SQLite telemetry is configured, but no ledger has been created yet.",
                "Run one DreamTeam task after confirming strict readiness.",
            )
        )
    else:
        diagnostics.append(
            Diagnostic("info", "LEDGER_PRESENT", "The metadata-only SQLite ledger is present.")
        )


def _select_run_id(
    connection: sqlite3.Connection,
    requested: str | None,
) -> tuple[str | None, tuple[str, str, str] | None]:
    rows = connection.execute(
        """
        SELECT run_id FROM run_metadata
        UNION SELECT run_id FROM checkpoints
        UNION SELECT run_id FROM reservations
        UNION SELECT run_id FROM charges
        UNION SELECT run_id FROM tool_events_v04
        UNION SELECT run_id FROM invalidations
        ORDER BY run_id
        """
    ).fetchall()
    run_ids = [str(row[0]) for row in rows]
    if requested is not None:
        if requested not in run_ids:
            return None, (
                "RUN_NOT_FOUND",
                f"Run {requested!r} is not present in the ledger.",
                "Pass --run <run-id> using the identifier emitted when the run was created.",
            )
        return requested, None
    if not run_ids:
        return None, (
            "NO_RUNS",
            "The ledger contains no run metadata.",
            "Run a telemetry-enabled DreamTeam task first.",
        )
    if len(run_ids) > 1:
        return None, (
            "RUN_ID_REQUIRED",
            f"The ledger contains {len(run_ids)} runs; an explicit run ID is required.",
            "Pass --run <run-id>.",
        )
    return run_ids[0], None


def _scalar(connection: sqlite3.Connection, query: str, run_id: str) -> int:
    row = connection.execute(query, (run_id,)).fetchone()
    return 0 if row is None else int(row[0])


def _unavailable_status(
    root: Path,
    ledger_path: Path | None,
    code: str,
    message: str,
    fix: str,
) -> StatusReport:
    return StatusReport(
        schema_version=REPORT_SCHEMA_VERSION,
        toolkit_version=__version__,
        available=False,
        project_root=str(root),
        ledger_path=None if ledger_path is None else str(ledger_path),
        run_id=None,
        config_hash=None,
        charged_usd_micros=0,
        reserved_usd_micros=0,
        active_workers=0,
        checkpoint_counts={},
        failed_tool_events=0,
        invalidation_categories=(),
        reason_code=code,
        message=message,
        fix=fix,
    )


if __name__ == "__main__":
    raise SystemExit(main())
