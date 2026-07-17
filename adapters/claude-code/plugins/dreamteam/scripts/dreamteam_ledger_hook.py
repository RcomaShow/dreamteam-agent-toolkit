#!/usr/bin/env python3
"""Claude Code hook for metadata-only reread, ownership, and budget enforcement."""
from __future__ import annotations

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

READ_COMMANDS = {"cat", "sed", "awk", "rg", "grep"}


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


def _load_config(cwd: Path) -> RuntimeConfig | None:
    path = cwd / "dreamteam.config.json"
    if not path.is_file():
        return None
    return RuntimeConfig.from_file(path)


def _blob(cwd: Path, relative: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), "hash-object", "--", relative],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git hash-object failed")
    return result.stdout.strip()


def _read_event(data: dict[str, Any], cwd: Path, reason: str) -> ReadEvent | None:
    tool = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    owner = "worker" if data.get("agent_id") else "main"
    agent_id = str(data.get("agent_id") or "main")
    run_id = str(os.environ.get("DREAMTEAM_RUN_ID") or data.get("session_id") or "unknown")
    if tool == "Read":
        raw_path = tool_input.get("file_path") or tool_input.get("path")
        if not isinstance(raw_path, str):
            return None
        target = Path(raw_path)
        if target.is_absolute():
            try:
                relative = target.resolve().relative_to(cwd.resolve()).as_posix()
            except ValueError:
                return None
        else:
            relative = target.as_posix()
        file_path = cwd / relative
        text = file_path.read_text(encoding="utf-8")
        start_line = int(tool_input.get("offset", 1) or 1)
        limit = tool_input.get("limit")
        end_line = len(text.splitlines()) if limit is None else min(len(text.splitlines()), start_line + int(limit) - 1)
        start, end = line_range_to_offsets(text, start_line, end_line)
        return ReadEvent(run_id, agent_id, owner, relative, _blob(cwd, relative), start, end, reason)
    if tool == "Bash":
        command = tool_input.get("command")
        path = _simple_bash_read_path(command)
        if path is None:
            return None
        target = Path(path)
        relative = target.resolve().relative_to(cwd.resolve()).as_posix() if target.is_absolute() else target.as_posix()
        content = (cwd / relative).read_bytes()
        return ReadEvent(run_id, agent_id, owner, relative, _blob(cwd, relative), 0, len(content), reason)
    return None


def _simple_bash_read_path(command: Any) -> str | None:
    if not isinstance(command, str) or any(marker in command for marker in ("&&", "||", ";", "|", ">", "<")):
        return None
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    executable = Path(parts[0]).name
    if executable in READ_COMMANDS:
        candidates = [part for part in parts[1:] if not part.startswith("-") and Path(part).suffix]
        return candidates[-1] if candidates else None
    if executable == "git" and len(parts) >= 3 and parts[1] in {"show", "diff"}:
        return None
    return None


def handle(data: dict[str, Any], phase: str, env: dict[str, str] | None = None) -> dict[str, object] | None:
    env = os.environ if env is None else env
    cwd = Path(str(data.get("cwd") or env.get("CLAUDE_PROJECT_DIR") or ".")).resolve()
    config = _load_config(cwd)
    if config is None or not config.telemetry.enabled or config.telemetry.ledger != "sqlite":
        return None
    data_dir = Path(env.get("CLAUDE_PLUGIN_DATA", str(cwd / ".dreamteam")))
    data_dir.mkdir(parents=True, exist_ok=True)
    ledger = RunLedger(data_dir / "ledger.sqlite")
    try:
        event_name = str(data.get("hook_event_name") or "")
        tool_name = str(data.get("tool_name") or "")
        run_id = str(env.get("DREAMTEAM_RUN_ID") or data.get("session_id") or "unknown")
        agent_id = str(data.get("agent_id") or "main")
        strict = config.telemetry.enforcement == "strict"

        if phase == "pre":
            if tool_name == "Agent" and data.get("agent_id"):
                return _deny("DreamTeam workers may not spawn agents; dispatch is owned by the root session")
            if tool_name == "Agent" and strict:
                expected = env.get("DREAMTEAM_NEXT_AGENT_USD_MICROS")
                if expected is None:
                    return _deny("strict mode requires DREAMTEAM_NEXT_AGENT_USD_MICROS before Agent dispatch")
                limit = int(config.budgets.max_run_usd * 1_000_000)
                node_id = str((data.get("tool_input") or {}).get("description") or "agent-dispatch")
                if not ledger.reserve(run_id, node_id, int(expected), limit):
                    return _deny("DreamTeam run budget reservation failed")
            reason = env.get("DREAMTEAM_READ_REASON", "explore" if data.get("agent_id") else "verify")
            try:
                event = _read_event(data, cwd, reason)
            except (OSError, ValueError, RuntimeError):
                event = None
            if event is not None and event.owner == "main":
                predicted = ledger.main_reread_ratio(run_id, event)
                if predicted > float(config.routing.max_main_reread_ratio):
                    if ledger.consume_permit(run_id, event.agent_id, event.path):
                        return _context(event_name or "PreToolUse", "DreamTeam decision-critical reread permit consumed")
                    message = f"DreamTeam reread ratio would reach {predicted:.3f}, above {config.routing.max_main_reread_ratio}"
                    return _deny(message) if strict else _context(event_name or "PreToolUse", message)
            if tool_name == "Bash" and strict:
                command = (data.get("tool_input") or {}).get("command")
                if isinstance(command, str) and any(token in command for token in ("cat ", "sed ", "awk ", "rg ", "grep ", "git show", "git diff", "open(")) and _simple_bash_read_path(command) is None:
                    ledger.invalidate(run_id, agent_id, "unaccountable_bash_read", command[:500])
                    return _deny("strict benchmark mode cannot account for this Bash read")
            return None

        if phase in {"post", "failure"}:
            reason = env.get("DREAMTEAM_READ_REASON", "explore" if data.get("agent_id") else "verify")
            try:
                event = _read_event(data, cwd, reason)
            except (OSError, ValueError, RuntimeError):
                event = None
            if event is not None:
                ledger.record_read(event)
            elif strict and tool_name in {"Grep", "Glob", "Bash"}:
                ledger.invalidate(run_id, agent_id, "unaccounted_tool_read", tool_name)
            return None

        if phase == "subagent-start":
            ledger.checkpoint(run_id, agent_id, "RUNNING")
        elif phase == "subagent-stop":
            ledger.checkpoint(run_id, agent_id, "DONE")
        return None
    finally:
        ledger.close()


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"pre", "post", "failure", "subagent-start", "subagent-stop"}:
        raise SystemExit("usage: dreamteam_ledger_hook.py <pre|post|failure|subagent-start|subagent-stop>")
    data = json.load(sys.stdin)
    result = handle(data, sys.argv[1])
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
