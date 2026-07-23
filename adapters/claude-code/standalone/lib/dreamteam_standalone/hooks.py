"""Claude Code settings and hook projection helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .filesystem import read_json_object, transform_text
from .model import StandaloneInstallError, string_key_mapping


def load_transformed_hooks(
    path: Path,
    *,
    runtime_root: Path,
    python_command: str,
) -> dict[str, list[dict[str, object]]]:
    data = read_json_object(path, missing_ok=False)
    raw_hooks = data.get("hooks")
    if not isinstance(raw_hooks, dict):
        raise StandaloneInstallError("hooks.json must contain an object named hooks")
    hooks: dict[str, list[dict[str, object]]] = {}
    for event, raw_entries in raw_hooks.items():
        if not isinstance(event, str) or not isinstance(raw_entries, list):
            raise StandaloneInstallError("invalid hook event")
        entries: list[dict[str, object]] = []
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                raise StandaloneInstallError("invalid hook entry")
            entry = transform_json_value(
                string_key_mapping(raw_entry, "hook entry"),
                runtime_root=runtime_root,
                python_command=python_command,
            )
            if not isinstance(entry, dict):
                raise AssertionError("hook transformation changed object type")
            entries.append(string_key_mapping(entry, "hook entry"))
        hooks[event] = entries
    return hooks


def transform_json_value(
    value: object,
    *,
    runtime_root: Path,
    python_command: str,
) -> object:
    if isinstance(value, str):
        return transform_text(
            value,
            runtime_root=runtime_root,
            python_command=python_command,
            standalone_skill=None,
            hooks_enabled=True,
        )
    if isinstance(value, list):
        return [
            transform_json_value(
                item,
                runtime_root=runtime_root,
                python_command=python_command,
            )
            for item in value
        ]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise StandaloneInstallError("JSON object keys must be strings")
            result[key] = transform_json_value(
                item,
                runtime_root=runtime_root,
                python_command=python_command,
            )
        return result
    return value


def merge_hooks(
    settings: dict[str, object],
    hooks: Mapping[str, list[dict[str, object]]],
) -> dict[str, list[dict[str, object]]]:
    raw_settings_hooks = settings.get("hooks")
    if raw_settings_hooks is None:
        settings_hooks: dict[str, object] = {}
        settings["hooks"] = settings_hooks
    elif isinstance(raw_settings_hooks, dict):
        settings_hooks = string_key_mapping(raw_settings_hooks, "settings hooks")
        settings["hooks"] = settings_hooks
    else:
        raise StandaloneInstallError("settings hooks must be an object")
    inserted: dict[str, list[dict[str, object]]] = {}
    for event, entries in hooks.items():
        raw_existing = settings_hooks.get(event)
        if raw_existing is None:
            existing: list[object] = []
            settings_hooks[event] = existing
        elif isinstance(raw_existing, list):
            existing = raw_existing
        else:
            raise StandaloneInstallError(f"settings hook event must be an array: {event}")
        for entry in entries:
            if entry not in existing:
                existing.append(entry)
                inserted.setdefault(event, []).append(entry)
    return inserted


def remove_tracked_hooks(
    settings: dict[str, object],
    hooks: Mapping[str, list[dict[str, object]]],
) -> bool:
    raw_settings_hooks = settings.get("hooks")
    if not isinstance(raw_settings_hooks, dict):
        return False
    settings_hooks = string_key_mapping(raw_settings_hooks, "settings hooks")
    changed = False
    for event, tracked_entries in hooks.items():
        raw_existing = settings_hooks.get(event)
        if not isinstance(raw_existing, list):
            continue
        existing = list(raw_existing)
        filtered = list(existing)
        for tracked in tracked_entries:
            try:
                filtered.remove(tracked)
            except ValueError:
                continue
        if filtered != existing:
            changed = True
            if filtered:
                settings_hooks[event] = filtered
            else:
                settings_hooks.pop(event, None)
    if not settings_hooks:
        if "hooks" in settings:
            settings.pop("hooks", None)
            changed = True
    else:
        settings["hooks"] = settings_hooks
    return changed


def remove_related_hooks(settings: dict[str, object], runtime_root: Path) -> bool:
    raw_settings_hooks = settings.get("hooks")
    if not isinstance(raw_settings_hooks, dict):
        return False
    settings_hooks = string_key_mapping(raw_settings_hooks, "settings hooks")
    runtime = runtime_root.resolve(strict=False).as_posix()
    changed = False
    for event, raw_entries in list(settings_hooks.items()):
        if not isinstance(raw_entries, list):
            continue
        filtered: list[object] = []
        for entry in raw_entries:
            encoded = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            if runtime in encoded:
                changed = True
                continue
            filtered.append(entry)
        if filtered:
            settings_hooks[event] = filtered
        else:
            settings_hooks.pop(event, None)
    if settings_hooks:
        settings["hooks"] = settings_hooks
    elif "hooks" in settings:
        settings.pop("hooks", None)
        changed = True
    return changed


def missing_hooks(
    settings: Mapping[str, object],
    hooks: Mapping[str, list[dict[str, object]]],
) -> list[str]:
    raw_settings_hooks = settings.get("hooks")
    if not isinstance(raw_settings_hooks, dict):
        return sorted(hooks)
    missing: list[str] = []
    for event, tracked_entries in hooks.items():
        existing = raw_settings_hooks.get(event)
        if not isinstance(existing, list) or any(
            entry not in existing for entry in tracked_entries
        ):
            missing.append(event)
    return missing
