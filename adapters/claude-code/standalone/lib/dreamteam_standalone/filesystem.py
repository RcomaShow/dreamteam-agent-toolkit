"""Filesystem projection and integrity helpers for the standalone adapter."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Mapping

from .model import (
    ADAPTER_ID,
    COMMAND_NAMES,
    InstallState,
    PLUGIN_ROOT_TOKEN,
    REQUIRED_PLUGIN_PATHS,
    RUNTIME_RELATIVE_PATH,
    STATE_RELATIVE_PATH,
    STATE_SCHEMA_VERSION,
    StandaloneInstallError,
    digest,
    json_bytes,
    string_key_mapping,
)


def source_plugin_root(explicit: str | Path | None) -> Path:
    candidate = (
        Path(explicit).expanduser()
        if explicit is not None
        else Path(__file__).resolve().parents[3] / "plugins/dreamteam"
    )
    if candidate.is_symlink():
        raise StandaloneInstallError("plugin source may not be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise StandaloneInstallError(f"plugin source does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise StandaloneInstallError("plugin source must be a regular directory")
    for relative in REQUIRED_PLUGIN_PATHS:
        if not (resolved / relative).exists():
            raise StandaloneInstallError(f"plugin source is missing: {relative.as_posix()}")
    return resolved


def claude_root(
    scope: str,
    *,
    project_root: str | Path | None,
    home: str | Path | None,
) -> Path:
    if scope == "project":
        base = Path.cwd() if project_root is None else Path(project_root).expanduser()
    elif scope == "user":
        base = Path.home() if home is None else Path(home).expanduser()
    else:
        raise StandaloneInstallError("scope must be 'project' or 'user'")
    base = base.resolve()
    if not base.is_dir():
        raise StandaloneInstallError(f"installation base is not a directory: {base}")
    return base / ".claude"


def validate_claude_root(path: Path) -> None:
    reject_symlink(path, "Claude configuration root")
    if path.exists() and not path.is_dir():
        raise StandaloneInstallError(
            f"Claude configuration root is not a directory: {path}"
        )


def plugin_version(plugin_root: Path) -> str:
    manifest = read_json_object(plugin_root / ".claude-plugin/plugin.json", missing_ok=False)
    if manifest.get("name") != "dreamteam":
        raise StandaloneInstallError("plugin manifest name must be dreamteam")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise StandaloneInstallError("plugin manifest version is missing")
    return version


def build_payload(
    plugin_root: Path,
    *,
    runtime_root: Path,
    python_command: str,
    adapter_version: str,
    hooks_enabled: bool,
) -> dict[Path, bytes]:
    payload: dict[Path, bytes] = {}
    for source in regular_files(plugin_root):
        relative = source.relative_to(plugin_root)
        if relative in {Path("adapter.json"), Path("install-state.json")}:
            continue
        raw = source.read_bytes()
        if source.suffix.lower() in {".json", ".md", ".py", ".txt"}:
            raw = transform_command_names(raw.decode("utf-8")).encode("utf-8")
        payload[RUNTIME_RELATIVE_PATH / relative] = raw
    payload[RUNTIME_RELATIVE_PATH / "adapter.json"] = json_bytes(
        {
            "adapter": ADAPTER_ID,
            "schemaVersion": STATE_SCHEMA_VERSION,
            "version": adapter_version,
        }
    )

    for source in regular_files(plugin_root / "agents"):
        if source.suffix == ".md":
            payload[Path("agents") / f"dreamteam-{source.name}"] = source.read_bytes()

    skills_root = plugin_root / "skills"
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        destination_root = Path("skills") / f"dreamteam-{skill_dir.name}"
        for source in regular_files(skill_dir):
            relative = source.relative_to(skill_dir)
            raw = source.read_bytes()
            if source.suffix.lower() in {".md", ".json", ".txt"}:
                raw = transform_text(
                    raw.decode("utf-8"),
                    runtime_root=runtime_root,
                    python_command=python_command,
                    standalone_skill=skill_dir.name if source.name == "SKILL.md" else None,
                    hooks_enabled=hooks_enabled,
                ).encode("utf-8")
            payload[destination_root / relative] = raw
    return payload


def regular_files(root: Path) -> list[Path]:
    if root.is_symlink() or not root.is_dir():
        raise StandaloneInstallError(f"source directory is invalid: {root}")
    excluded_parts = {".git", "__pycache__", ".pytest_cache", "dist", ".dreamteam"}
    excluded_suffixes = {".pyc", ".pyo"}
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise StandaloneInstallError(f"standalone source refuses symlink: {path}")
        relative = path.relative_to(root)
        if excluded_parts.intersection(relative.parts) or path.suffix in excluded_suffixes:
            continue
        if path.is_file():
            files.append(path)
    return files


def transform_text(
    text: str,
    *,
    runtime_root: Path,
    python_command: str,
    standalone_skill: str | None,
    hooks_enabled: bool,
) -> str:
    if standalone_skill == "doctor" and not hooks_enabled:
        text = text.replace(
            f' --plugin-root "{PLUGIN_ROOT_TOKEN}" --hooks-available',
            "",
        )
    runtime = command_literal(
        runtime_root.resolve(strict=False).as_posix(),
        "standalone runtime path",
    )
    python = quote_command(python_command)
    text = text.replace(
        f'python3 "{PLUGIN_ROOT_TOKEN}',
        f'{python} "{runtime}',
    )
    text = text.replace(PLUGIN_ROOT_TOKEN, runtime)
    text = transform_command_names(text)
    if standalone_skill is not None:
        text = replace_skill_name(text, f"dreamteam-{standalone_skill}")
    return text


def replace_skill_name(text: str, name: str) -> str:
    if not text.startswith("---\n"):
        raise StandaloneInstallError("skill is missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise StandaloneInstallError("skill has unterminated YAML frontmatter")
    frontmatter = text[4:end]
    replaced, count = re.subn(
        r"(?m)^name:\s*[^\n]+$",
        f"name: {name}",
        frontmatter,
        count=1,
    )
    if count != 1:
        raise StandaloneInstallError("skill frontmatter is missing name")
    return "---\n" + replaced + text[end:]


def transform_command_names(text: str) -> str:
    for name in COMMAND_NAMES:
        text = text.replace(f"/dreamteam:{name}", f"/dreamteam-{name}")
    return text


def command_literal(value: str, label: str) -> str:
    forbidden = ("\x00", "\r", "\n", '"', "`", "$", "%", "!", "\\")
    if not value or any(marker in value for marker in forbidden):
        raise StandaloneInstallError(f"{label} contains unsupported shell characters")
    return value


def quote_command(command: str) -> str:
    if Path(command).is_absolute():
        command = Path(command).as_posix()
    return f'"{command_literal(command, "Python command")}"'


def read_json_object(path: Path, *, missing_ok: bool) -> dict[str, object]:
    reject_symlink(path, f"JSON file {path}")
    if not path.exists():
        if missing_ok:
            return {}
        raise StandaloneInstallError(f"JSON file does not exist: {path}")
    if not path.is_file():
        raise StandaloneInstallError(f"JSON path is not a regular file: {path}")
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StandaloneInstallError(f"cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StandaloneInstallError(f"JSON root must be an object: {path}")
    return string_key_mapping(value, f"JSON file {path}")


def load_state(path: Path, *, required: bool) -> InstallState | None:
    if path.is_symlink():
        raise StandaloneInstallError("install-state may not be a symlink")
    if not path.exists():
        if required:
            raise StandaloneInstallError(f"standalone install-state was not found: {path}")
        return None
    return InstallState.from_mapping(read_json_object(path, missing_ok=False))


def assert_state_targets(state: InstallState, root: Path, scope: str) -> None:
    if state.scope != scope:
        raise StandaloneInstallError("install-state scope does not match requested scope")
    if Path(state.claude_root) != root:
        raise StandaloneInstallError("install-state Claude root does not match requested scope")
    if Path(state.runtime_root) != root / RUNTIME_RELATIVE_PATH:
        raise StandaloneInstallError("install-state runtime root is inconsistent")
    if Path(state.settings_path) != root / "settings.json":
        raise StandaloneInstallError("install-state settings path is inconsistent")


def preflight_destinations(
    root: Path,
    payload: Mapping[Path, bytes],
    previous_files: Mapping[str, str],
    *,
    force: bool,
) -> None:
    for relative, content in payload.items():
        destination = safe_destination(root, relative)
        reject_symlink(destination, f"destination {relative.as_posix()}")
        if not destination.exists():
            continue
        if not destination.is_file():
            raise StandaloneInstallError(
                f"destination is not a regular file: {relative.as_posix()}"
            )
        tracked = relative.as_posix() in previous_files
        if not tracked and not force:
            raise StandaloneInstallError(
                f"destination already exists outside standalone state: {relative.as_posix()}"
            )


def verify_tracked_files(
    root: Path,
    files: Mapping[str, str],
    *,
    force: bool,
) -> None:
    for relative, expected in files.items():
        target = safe_destination(root, Path(relative))
        if target.is_symlink() or not target.is_file():
            if force:
                continue
            raise StandaloneInstallError(f"tracked file is unavailable: {relative}")
        if digest(target.read_bytes()) != expected and not force:
            raise StandaloneInstallError(f"tracked file was modified: {relative}")


def remove_files(
    root: Path,
    files: Mapping[str, str],
    *,
    force: bool,
) -> None:
    for relative in sorted(files, key=lambda item: (item.count("/"), item), reverse=True):
        target = safe_destination(root, Path(relative))
        if target.is_symlink():
            if not force:
                raise StandaloneInstallError(f"refusing to remove symlink: {relative}")
            target.unlink(missing_ok=True)
            continue
        if target.exists():
            if not target.is_file():
                raise StandaloneInstallError(f"refusing to remove non-file: {relative}")
            target.unlink()
        prune_empty_directories(target.parent, stop=root)


def safe_destination(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise StandaloneInstallError(f"invalid relative destination: {relative}")
    candidate = root.joinpath(relative)
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise StandaloneInstallError(f"destination parent is a symlink: {current}")
    return candidate


def reject_symlink(path: Path, label: str) -> None:
    if path.is_symlink():
        raise StandaloneInstallError(f"{label} may not be a symlink")


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_symlink(path, f"destination {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            temporary = Path(stream.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def prune_empty_directories(path: Path, *, stop: Path) -> None:
    current = path
    while current != stop and current.is_relative_to(stop):
        if not current.exists() or current.is_symlink() or not current.is_dir():
            current = current.parent
            continue
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent
