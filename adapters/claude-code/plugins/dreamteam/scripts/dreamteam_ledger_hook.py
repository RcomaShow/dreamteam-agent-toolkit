#!/usr/bin/env python3
"""Claude Code hook for fail-closed scope, protocol, and budget enforcement."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "lib"))

from dreamteam.config import RuntimeConfig
from dreamteam.ledger import ReadEvent, RunLedger, line_range_to_offsets
from dreamteam.protocol import ProtocolError, protocol_identity, validate

READ_COMMANDS = {"cat", "sed", "awk", "rg", "grep", "head", "tail", "less", "more"}
DANGEROUS_EXECUTABLES = {
    "chmod",
    "chown",
    "curl",
    "dd",
    "doas",
    "ftp",
    "mount",
    "nc",
    "netcat",
    "powershell",
    "pwsh",
    "rm",
    "scp",
    "ssh",
    "sudo",
    "umount",
    "wget",
}
DANGEROUS_GIT_SUBCOMMANDS = {
    "clean",
    "clone",
    "config",
    "fetch",
    "gc",
    "push",
    "remote",
    "reset",
    "restore",
    "submodule",
    "worktree",
}
PROTECTED_CONFIG = "dreamteam.config.json"
SHELL_CONTROL_MARKERS = ("&&", "||", ";", "|", ">", "<", "\n", "\r", "`", "$(", "&", ">(", "<(")
TRUSTED_PLUGIN_SCRIPTS = {
    "dreamteam_anchor.py",
    "dreamteam_measure.py",
    "dreamteam_protocol.py",
    "dreamteam_route.py",
}
DREAMTEAM_AGENT_TYPES = {
    "coordination-decision-analyst",
    "discovery-context-synthesizer",
    "discovery-flow-tracer",
    "discovery-impact-mapper",
    "discovery-pattern-miner",
    "discovery-symbol-locator",
    "execution-bounded-logic",
    "execution-documentation-updater",
    "execution-mechanical-editor",
    "execution-scaffold-builder",
    "execution-sonnet-lead",
    "execution-test-writer",
    "verification-diff-auditor",
    "verification-failure-triage",
    "verification-independent-reviewer",
    "verification-test-gap-finder",
}


def _deny(reason: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _context(event: str, message: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}}


def _block_subagent(reason: str) -> dict[str, object]:
    return {"decision": "block", "reason": reason}


def _project_root(data: dict[str, Any], env: dict[str, str]) -> Path:
    raw = env.get("CLAUDE_PROJECT_DIR") or data.get("project_dir") or data.get("cwd") or "."
    root = Path(str(raw)).resolve(strict=True)
    if not root.is_dir():
        raise PermissionError("project root is not a directory")
    return root


def _load_config(project_root: Path) -> tuple[RuntimeConfig | None, str | None]:
    path = project_root / PROTECTED_CONFIG
    if path.is_symlink():
        raise PermissionError("dreamteam.config.json may not be a symlink")
    if not path.exists():
        return None, None
    if not path.is_file():
        raise PermissionError("dreamteam.config.json must be a regular file")
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid DreamTeam configuration: {exc}") from exc
    if not isinstance(data, dict):
        raise TypeError("DreamTeam configuration root must be an object")
    return RuntimeConfig.from_mapping(data), sha256(raw).hexdigest()


def _normalize_requested_path(raw_path: str) -> Path:
    if not raw_path or "\x00" in raw_path:
        raise PermissionError("path must be a non-empty string without NUL bytes")
    normalized = raw_path.replace("\\", "/")
    requested = Path(normalized)
    if ".." in requested.parts:
        raise PermissionError("path traversal is not allowed")
    return requested


def _reject_symlink_components(project_root: Path, candidate: Path) -> None:
    try:
        relative = candidate.relative_to(project_root)
    except ValueError as exc:
        raise PermissionError("path resolves outside project root") from exc
    current = project_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PermissionError("symlink paths are not allowed")


def _resolve_project_path(
    project_root: Path,
    cwd: Path,
    raw_path: str,
    *,
    requirement: str,
) -> tuple[Path, str]:
    requested = _normalize_requested_path(raw_path)
    candidate = requested if requested.is_absolute() else cwd / requested
    # abspath normalizes '.' without following symlinks. Components are checked
    # before resolve() so a symlink cannot escape and then appear non-symlinked.
    lexical = Path(os.path.abspath(str(candidate)))
    _reject_symlink_components(project_root, lexical)
    try:
        relative = lexical.relative_to(project_root)
    except ValueError as exc:
        raise PermissionError("path resolves outside project root") from exc

    if requirement == "write":
        parent = lexical.parent
        _reject_symlink_components(project_root, parent)
        if not parent.is_dir():
            raise PermissionError("write parent must be an existing directory")
    elif requirement == "file":
        if not lexical.is_file():
            raise PermissionError("path is not an existing regular file")
    elif requirement == "existing":
        if not lexical.exists():
            raise PermissionError("path does not exist")
    else:
        raise ValueError(f"unsupported path requirement: {requirement}")
    return lexical, relative.as_posix()


def _internal_path_violation(
    project_root: Path,
    candidate: Path,
    data_dir: Path,
) -> str | None:
    try:
        relative = candidate.relative_to(project_root)
    except ValueError:
        return "path resolves outside project root"
    if relative.parts and relative.parts[0] == ".git":
        return "Git metadata is outside the DreamTeam tool boundary"
    data_lexical = Path(os.path.abspath(str(data_dir)))
    try:
        candidate.relative_to(data_lexical)
    except ValueError:
        return None
    return "DreamTeam plugin data is outside the agent tool boundary"


def _blob(project_root: Path, relative: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "hash-object", "--", relative],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git hash-object failed")
    value = result.stdout.strip()
    if not value:
        raise RuntimeError("git hash-object returned an empty blob id")
    return value


def _tool_path(tool: str, tool_input: dict[str, Any]) -> str | None:
    if tool in {"Read", "Edit", "Write"}:
        value = tool_input.get("file_path") or tool_input.get("path")
    elif tool in {"Grep", "Glob"}:
        value = tool_input.get("path")
    else:
        return None
    return value if isinstance(value, str) and value else None


def _validate_search_patterns(tool: str, tool_input: dict[str, Any]) -> None:
    names = ("pattern",) if tool == "Glob" else ("glob",)
    for name in names:
        value = tool_input.get(name)
        if value is None:
            continue
        if not isinstance(value, str) or not value:
            raise PermissionError(f"{tool}.{name} must be a non-empty string")
        requested = _normalize_requested_path(value)
        if requested.is_absolute():
            raise PermissionError(f"{tool}.{name} may not be absolute")


def _strict_positive_int(value: Any, name: str, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _read_event(
    data: dict[str, Any],
    project_root: Path,
    cwd: Path,
    reason: str,
    run_id: str,
    agent_id: str,
) -> ReadEvent | None:
    if data.get("tool_name") != "Read":
        return None
    tool_input = data.get("tool_input") or {}
    raw_path = _tool_path("Read", tool_input)
    if raw_path is None:
        raise ValueError("Read requires file_path")
    file_path, relative = _resolve_project_path(
        project_root,
        cwd,
        raw_path,
        requirement="file",
    )
    text = file_path.read_text(encoding="utf-8")
    if not text:
        return None
    lines = text.splitlines(keepends=True)
    start_line = _strict_positive_int(tool_input.get("offset"), "Read offset", 1)
    limit_raw = tool_input.get("limit")
    limit = None if limit_raw is None else _strict_positive_int(limit_raw, "Read limit")
    if start_line > len(lines):
        return None
    end_line = len(lines) if limit is None else min(len(lines), start_line + limit - 1)
    start, end = line_range_to_offsets(text, start_line, end_line)
    if end <= start:
        return None
    owner = "worker" if data.get("agent_id") else "main"
    return ReadEvent(
        run_id,
        agent_id,
        owner,
        relative,
        _blob(project_root, relative),
        start,
        end,
        reason,
    )


def _allowed_bash_hashes(env: dict[str, str]) -> set[str]:
    raw = env.get("DREAMTEAM_ALLOWED_BASH_SHA256", "")
    values: set[str] = set()
    for item in raw.replace(";", ",").split(","):
        value = item.strip().lower()
        if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
            values.add(value)
    return values


def _trusted_plugin_command(parts: list[str], env: dict[str, str]) -> bool:
    if len(parts) < 2 or Path(parts[0]).name.lower() not in {"python", "python3"}:
        return False
    raw_script = parts[1]
    plugin_root = Path(env.get("CLAUDE_PLUGIN_ROOT", str(PLUGIN))).resolve()
    for prefix in ("${CLAUDE_PLUGIN_ROOT}/", "$CLAUDE_PLUGIN_ROOT/"):
        if raw_script.startswith(prefix):
            raw_script = str(plugin_root / raw_script[len(prefix):])
            break
    script = Path(raw_script)
    if not script.is_absolute():
        return False
    try:
        relative = script.resolve(strict=False).relative_to(plugin_root)
    except ValueError:
        return False
    return (
        len(relative.parts) == 2
        and relative.parts[0] == "scripts"
        and relative.name in TRUSTED_PLUGIN_SCRIPTS
    )


def _bash_violation(command: Any, *, strict: bool, env: dict[str, str]) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return "Bash command must be a non-empty string"
    if any(marker in command for marker in SHELL_CONTROL_MARKERS):
        return "strict mode rejects shell composition, redirection, substitution, and background execution"
    try:
        parts = shlex.split(command)
    except ValueError:
        return "Bash command has invalid quoting"
    if not parts:
        return "Bash command is empty"
    executable = Path(parts[0]).name.lower()
    if executable in READ_COMMANDS:
        return "strict mode requires Read, Grep, or Glob instead of Bash file readers"
    if executable in DANGEROUS_EXECUTABLES:
        return f"strict mode rejects dangerous executable: {executable}"
    if executable == "git" and len(parts) >= 2:
        subcommand = parts[1].lower()
        if subcommand in {"show", "diff", "grep"}:
            return "strict mode rejects repository content reads through Bash"
        if subcommand in DANGEROUS_GIT_SUBCOMMANDS:
            return f"strict mode rejects dangerous git subcommand: {subcommand}"
    if executable in {"bash", "sh", "zsh", "fish", "xargs"}:
        return "strict mode rejects nested shells and command fan-out"
    if executable in {"python", "python3", "node", "ruby", "perl"} and any(
        part in {"-c", "-e", "-", "--eval"} for part in parts[1:]
    ):
        return "strict mode rejects inline interpreter execution"
    if strict and _trusted_plugin_command(parts, env):
        return None
    if strict:
        digest = sha256(command.encode("utf-8")).hexdigest()
        if digest not in _allowed_bash_hashes(env):
            return (
                "strict mode requires the exact Bash command SHA-256 in "
                "DREAMTEAM_ALLOWED_BASH_SHA256"
            )
    return None


def _metadata_hash(tool_name: str, tool_input: Any) -> str:
    payload = json.dumps(
        {"tool_name": tool_name, "tool_input": tool_input},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _redacted_detail(value: Any) -> str:
    return "sha256:" + sha256(str(value).encode("utf-8", errors="replace")).hexdigest()


def _identity(
    data: dict[str, Any],
    env: dict[str, str],
    *,
    strict: bool,
) -> tuple[str, str]:
    run_id = str(env.get("DREAMTEAM_RUN_ID") or data.get("session_id") or "")
    agent_id = str(data.get("agent_id") or "main")
    if strict and not run_id:
        raise ValueError("strict mode requires DREAMTEAM_RUN_ID or session_id")
    if not run_id:
        run_id = "advisory-unknown"
    return run_id, agent_id


def _tool_event_id(
    data: dict[str, Any],
    *,
    strict: bool,
    metadata_hash: str,
) -> str:
    value = data.get("tool_use_id")
    if isinstance(value, str) and value:
        return value
    if strict:
        raise ValueError("strict mode requires tool_use_id for tool events")
    session_id = str(data.get("session_id") or "advisory")
    return f"advisory-{sha256((session_id + metadata_hash).encode()).hexdigest()[:32]}"


def _active_reservation_limit(config: RuntimeConfig) -> int:
    return config.budgets.max_active_workers if config.routing.allow_parallel_independent else 1


def _validate_subagent_output(
    data: dict[str, Any],
    env: dict[str, str],
    project_root: Path,
    config: RuntimeConfig,
    ledger: RunLedger,
    run_id: str,
    agent_id: str,
    strict: bool,
) -> dict[str, object] | None:
    agent_type = str(data.get("agent_type") or "")
    if agent_type not in DREAMTEAM_AGENT_TYPES:
        ledger.checkpoint(run_id, agent_id, "DONE")
        return None
    message = data.get("last_assistant_message")
    errors: list[str] = []
    identity = None
    binding: tuple[str, str | None, str | None] | None = None
    if not isinstance(message, str) or not message.strip():
        errors.append("DreamTeam subagent must return a non-empty CHP/2 handoff")
    else:
        try:
            identity = protocol_identity(message)
            binding = ledger.contract_binding(run_id, identity.task_id)
        except (ProtocolError, ValueError) as exc:
            errors.append(str(exc))

        if strict and binding is None:
            errors.append("strict mode requires a registered DCP/2 binding for the CHP task")

        expected_run_id = env.get("DREAMTEAM_EXPECTED_RUN_ID") or run_id
        expected_task_id = env.get("DREAMTEAM_EXPECTED_TASK_ID")
        expected_contract_hash = env.get("DREAMTEAM_EXPECTED_CONTRACT_HASH")
        bound_author: str | None = None
        bound_reviewer: str | None = None
        if binding is not None:
            bound_hash, bound_author, bound_reviewer = binding
            expected_contract_hash = expected_contract_hash or bound_hash
            if identity is not None:
                expected_task_id = expected_task_id or identity.task_id

        configured_author = env.get("DREAMTEAM_AUTHOR_AGENT_ID") or bound_author
        identity_role = "author"
        if agent_type == "verification-independent-reviewer":
            identity_role = "reviewer"
            if bound_reviewer is not None and bound_reviewer != agent_id:
                errors.append("reviewer agent conflicts with the registered DCP binding")
            if strict and not configured_author:
                errors.append("independent review requires a registered author agent")
            reviewer_agent_id = agent_id
            author_agent_id = configured_author
        else:
            if bound_author is not None and bound_author != agent_id:
                errors.append("author agent conflicts with the registered DCP binding")
            author_agent_id = agent_id
            reviewer_agent_id = env.get("DREAMTEAM_REVIEWER_AGENT_ID") or bound_reviewer

        try:
            errors.extend(
                validate(
                    message,
                    require_anchors=config.verification.require_anchor_validation,
                    require_contract_hash=strict,
                    repo_root=project_root,
                    expected_run_id=expected_run_id,
                    expected_task_id=expected_task_id,
                    expected_contract_hash=expected_contract_hash,
                    author_agent_id=author_agent_id,
                    reviewer_agent_id=reviewer_agent_id,
                )
            )
        except ProtocolError as exc:
            errors.append(str(exc))
        if not errors and binding is not None and identity is not None:
            if not ledger.claim_contract_identity(
                run_id, identity.task_id, role=identity_role, agent_id=agent_id
            ):
                errors.append(
                    f"{identity_role} agent conflicts with the registered DCP binding"
                )
    if errors:
        detail = "; ".join(dict.fromkeys(errors[:8]))
        ledger.invalidate(run_id, agent_id, "invalid_handoff", _redacted_detail(detail))
        if strict and not bool(data.get("stop_hook_active")):
            return _block_subagent(f"DreamTeam CHP/2 validation failed: {detail}")
        ledger.checkpoint(run_id, agent_id, "FAILED")
        return None
    assert isinstance(message, str)
    ledger.checkpoint(run_id, agent_id, "DONE", sha256(message.encode("utf-8")).hexdigest())
    return None


def handle(
    data: dict[str, Any],
    phase: str,
    env: dict[str, str] | None = None,
) -> dict[str, object] | None:
    env = os.environ if env is None else env
    try:
        project_root = _project_root(data, env)
    except (OSError, PermissionError, ValueError) as exc:
        return _deny(f"DreamTeam project root is invalid: {exc}")
    cwd = Path(str(data.get("cwd") or project_root)).resolve()
    try:
        cwd.relative_to(project_root)
    except ValueError:
        return _deny("working directory resolves outside project root")

    data_dir = Path(env.get("CLAUDE_PLUGIN_DATA", str(project_root / ".dreamteam")))
    database = data_dir / "ledger.sqlite"
    run_hint = str(env.get("DREAMTEAM_RUN_ID") or data.get("session_id") or "")
    try:
        config, config_hash = _load_config(project_root)
    except (OSError, PermissionError, TypeError, ValueError) as exc:
        return _deny(f"DreamTeam configuration is invalid: {exc}")
    if config is None:
        if database.is_file() and run_hint:
            ledger = RunLedger(database)
            try:
                if ledger.config_hash_for_run(run_hint) is not None:
                    return _deny("DreamTeam configuration disappeared during the active run")
            finally:
                ledger.close()
        return None
    if not config.telemetry.enabled:
        return None
    if config.telemetry.ledger != "sqlite":
        return _deny("enabled DreamTeam telemetry requires the SQLite ledger")

    data_dir.mkdir(parents=True, exist_ok=True)
    ledger = RunLedger(database)
    try:
        event_name = str(data.get("hook_event_name") or "")
        tool_name = str(data.get("tool_name") or "")
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return _deny("tool_input must be an object")
        strict = config.telemetry.enforcement == "strict"
        try:
            run_id, agent_id = _identity(data, env, strict=strict)
        except ValueError as exc:
            return _deny(str(exc))

        if config_hash is None or not ledger.bind_config(run_id, config_hash):
            message = "DreamTeam configuration changed during the active run"
            return _deny(message) if strict else _context(event_name or "PreToolUse", message)

        if phase == "pre":
            if tool_name in {"Grep", "Glob"}:
                try:
                    _validate_search_patterns(tool_name, tool_input)
                except PermissionError as exc:
                    message = f"DreamTeam search policy rejected the tool request: {exc}"
                    return _deny(message) if strict else _context(event_name or "PreToolUse", message)

            path = _tool_path(tool_name, tool_input)
            if path is not None:
                requirement = {
                    "Read": "file",
                    "Edit": "file",
                    "Write": "write",
                    "Grep": "existing",
                    "Glob": "existing",
                }.get(tool_name)
                assert requirement is not None
                try:
                    candidate, relative = _resolve_project_path(
                        project_root,
                        cwd,
                        path,
                        requirement=requirement,
                    )
                except (OSError, PermissionError, ValueError) as exc:
                    message = f"DreamTeam path policy rejected the tool request: {exc}"
                    return _deny(message) if strict else _context(event_name or "PreToolUse", message)
                internal_violation = _internal_path_violation(
                    project_root, candidate, data_dir
                )
                if internal_violation:
                    return (
                        _deny(internal_violation)
                        if strict
                        else _context(event_name or "PreToolUse", internal_violation)
                    )
                if tool_name in {"Edit", "Write"} and relative == PROTECTED_CONFIG:
                    message = "dreamteam.config.json is immutable during a run"
                    return _deny(message) if strict else _context(event_name or "PreToolUse", message)

            if tool_name == "Agent" and data.get("agent_id"):
                return _deny("DreamTeam workers may not spawn agents; dispatch is owned by the root session")

            metadata_hash = _metadata_hash(tool_name, tool_input)
            try:
                tool_use_id = _tool_event_id(data, strict=strict, metadata_hash=metadata_hash)
            except ValueError as exc:
                return _deny(str(exc))

            if tool_name == "Agent" and strict:
                expected = env.get("DREAMTEAM_NEXT_AGENT_USD_MICROS")
                if expected is None:
                    return _deny("strict mode requires DREAMTEAM_NEXT_AGENT_USD_MICROS before Agent dispatch")
                try:
                    expected_micros = int(expected)
                    if expected_micros < 0:
                        raise ValueError
                except ValueError:
                    return _deny("DREAMTEAM_NEXT_AGENT_USD_MICROS must be a non-negative integer")
                limit = int(config.budgets.max_run_usd * 1_000_000)
                try:
                    reserved = ledger.reserve(
                        run_id,
                        tool_use_id,
                        expected_micros,
                        limit,
                        max_active_reservations=_active_reservation_limit(config),
                    )
                except (TypeError, ValueError) as exc:
                    return _deny(f"invalid DreamTeam budget reservation: {exc}")
                if not reserved:
                    return _deny("DreamTeam run budget or active-worker reservation failed")

            if tool_name == "Bash":
                violation = _bash_violation(
                    tool_input.get("command"),
                    strict=strict,
                    env=env,
                )
                if violation:
                    ledger.invalidate(
                        run_id,
                        agent_id,
                        "bash_policy",
                        _redacted_detail(tool_input.get("command")),
                    )
                    return _deny(violation) if strict else _context(event_name or "PreToolUse", violation)

            reason = env.get(
                "DREAMTEAM_READ_REASON",
                "explore" if data.get("agent_id") else "verify",
            )
            try:
                event = _read_event(
                    data,
                    project_root,
                    cwd,
                    reason,
                    run_id,
                    agent_id,
                )
            except (OSError, PermissionError, UnicodeError, ValueError, RuntimeError) as exc:
                if tool_name == "Read":
                    message = f"DreamTeam cannot account for this Read: {exc}"
                    return _deny(message) if strict else _context(event_name or "PreToolUse", message)
                event = None
            pre_context: dict[str, object] | None = None
            if event is not None and event.owner == "main":
                predicted = ledger.main_reread_ratio(run_id, event)
                if predicted > float(config.routing.max_main_reread_ratio):
                    if ledger.consume_permit(run_id, event.agent_id, event.path):
                        pre_context = _context(
                            event_name or "PreToolUse",
                            "DreamTeam decision-critical reread permit consumed",
                        )
                    else:
                        message = (
                            f"DreamTeam reread ratio would reach {predicted:.3f}, "
                            f"above {config.routing.max_main_reread_ratio}"
                        )
                        if strict:
                            return _deny(message)
                        pre_context = _context(event_name or "PreToolUse", message)

            if event is not None:
                ledger.stage_read(tool_use_id, event)
            ledger.record_tool_event(
                run_id,
                agent_id,
                tool_use_id,
                tool_name or "unknown",
                "requested",
                metadata_hash,
            )
            return pre_context

        if phase in {"post", "failure"}:
            metadata_hash = _metadata_hash(tool_name, tool_input)
            try:
                tool_use_id = _tool_event_id(data, strict=strict, metadata_hash=metadata_hash)
            except ValueError:
                ledger.invalidate(run_id, agent_id, "missing_tool_use_id", metadata_hash)
                return None
            status = "completed" if phase == "post" else "failed"
            if tool_name == "Agent":
                if phase == "post":
                    ledger.commit_reservation(run_id, tool_use_id)
                else:
                    ledger.release(run_id, tool_use_id)
            post_context: dict[str, object] | None = None
            if phase == "post":
                pending = ledger.pending_read(run_id, tool_use_id)
                if pending is not None:
                    try:
                        current_blob = _blob(project_root, pending.path)
                        committed = ledger.commit_staged_read(
                            run_id,
                            tool_use_id,
                            current_blob_id=current_blob,
                        )
                    except (OSError, RuntimeError, ValueError):
                        committed = False
                        ledger.discard_staged_read(run_id, tool_use_id)
                    if not committed:
                        ledger.invalidate(
                            run_id, agent_id, "read_changed_during_tool", metadata_hash
                        )
                        post_context = _context(
                            event_name or "PostToolUse",
                            "DreamTeam invalidated the Read because its blob changed during tool execution",
                        )
            else:
                ledger.discard_staged_read(run_id, tool_use_id)
                ledger.invalidate(run_id, agent_id, "tool_failure", metadata_hash)
            ledger.record_tool_event(
                run_id,
                agent_id,
                tool_use_id,
                tool_name or "unknown",
                status,
                metadata_hash,
            )
            return post_context

        if phase == "subagent-start":
            ledger.checkpoint(run_id, agent_id, "RUNNING")
            return None
        if phase == "subagent-stop":
            return _validate_subagent_output(
                data,
                env,
                project_root,
                config,
                ledger,
                run_id,
                agent_id,
                strict,
            )
        return None
    finally:
        ledger.close()


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {
        "pre",
        "post",
        "failure",
        "subagent-start",
        "subagent-stop",
    }:
        raise SystemExit(
            "usage: dreamteam_ledger_hook.py <pre|post|failure|subagent-start|subagent-stop>"
        )
    data = json.load(sys.stdin)
    if not isinstance(data, dict):
        raise TypeError("hook input must be a JSON object")
    result = handle(data, sys.argv[1])
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
