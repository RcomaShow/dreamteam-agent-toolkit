"""Standalone adapter installation and upgrade."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

from .filesystem import (
    assert_state_targets,
    atomic_write,
    build_payload,
    claude_root,
    load_state,
    plugin_version,
    preflight_destinations,
    read_json_object,
    remove_files,
    safe_destination,
    source_plugin_root,
    validate_claude_root,
    verify_tracked_files,
)
from .hooks import (
    load_transformed_hooks,
    merge_hooks,
    missing_hooks,
    remove_related_hooks,
    remove_tracked_hooks,
)
from .model import (
    ADAPTER_ID,
    RUNTIME_RELATIVE_PATH,
    STATE_RELATIVE_PATH,
    STATE_SCHEMA_VERSION,
    InstallResult,
    InstallState,
    StandaloneInstallError,
    digest,
    json_bytes,
)


def install(
    *,
    scope: str,
    project_root: str | Path | None = None,
    home: str | Path | None = None,
    source_plugin_root_path: str | Path | None = None,
    enable_hooks: bool = False,
    force: bool = False,
    dry_run: bool = False,
    python_command: str | None = None,
) -> InstallResult:
    """Install or upgrade the adapter into a Claude Code configuration root."""
    if type(enable_hooks) is not bool or type(force) is not bool or type(dry_run) is not bool:
        raise TypeError("enable_hooks, force, and dry_run must be booleans")
    plugin_root = source_plugin_root(source_plugin_root_path)
    root = claude_root(scope, project_root=project_root, home=home)
    validate_claude_root(root)
    runtime_root = root / RUNTIME_RELATIVE_PATH
    settings_path = root / "settings.json"
    state_path = safe_destination(root, STATE_RELATIVE_PATH)
    executable = python_command or sys.executable
    if not executable:
        raise StandaloneInstallError("a Python executable is required")

    previous = load_state(state_path, required=False)
    if previous is not None:
        assert_state_targets(previous, root, scope)
        verify_tracked_files(root, previous.files, force=force)

    adapter_version = plugin_version(plugin_root)
    payload = build_payload(
        plugin_root,
        runtime_root=runtime_root,
        python_command=executable,
        adapter_version=adapter_version,
        hooks_enabled=enable_hooks,
    )
    previous_files = {} if previous is None else previous.files
    preflight_destinations(root, payload, previous_files, force=force)

    settings_existed = settings_path.is_file()
    previous_hooks = {} if previous is None else previous.managed_hooks
    settings: dict[str, object] = {}
    settings_before: dict[str, object] = {}
    if enable_hooks or previous_hooks:
        settings = read_json_object(settings_path, missing_ok=True)
        settings_before = deepcopy(settings)
        missing_previous = missing_hooks(settings, previous_hooks)
        if missing_previous and not force:
            raise StandaloneInstallError(
                "tracked standalone hooks were modified or removed: "
                + ", ".join(missing_previous)
            )
        if missing_previous:
            remove_related_hooks(settings, runtime_root)
        else:
            remove_tracked_hooks(settings, previous_hooks)

    expected_hooks: dict[str, list[dict[str, object]]] = {}
    managed_hooks: dict[str, list[dict[str, object]]] = {}
    if enable_hooks:
        expected_hooks = load_transformed_hooks(
            plugin_root / "hooks/hooks.json",
            runtime_root=runtime_root,
            python_command=executable,
        )
        managed_hooks = merge_hooks(settings, expected_hooks)
    settings_changed = settings != settings_before

    file_hashes = {path.as_posix(): digest(content) for path, content in payload.items()}
    state = InstallState(
        schema_version=STATE_SCHEMA_VERSION,
        adapter=ADAPTER_ID,
        adapter_version=adapter_version,
        scope=scope,
        claude_root=str(root),
        runtime_root=str(runtime_root),
        settings_path=str(settings_path),
        settings_existed=settings_existed if previous is None else previous.settings_existed,
        hooks_enabled=enable_hooks,
        files=file_hashes,
        expected_hooks=expected_hooks,
        managed_hooks=managed_hooks,
    )

    action = "planned" if dry_run else ("upgraded" if previous is not None else "installed")
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        if previous is not None:
            stale = set(previous.files) - set(file_hashes)
            remove_files(
                root,
                {path: previous.files[path] for path in stale},
                force=force,
            )
        for relative, content in sorted(payload.items(), key=lambda item: item[0].as_posix()):
            atomic_write(safe_destination(root, relative), content)
        if settings_changed:
            if not state.settings_existed and not settings:
                settings_path.unlink(missing_ok=True)
            else:
                atomic_write(settings_path, json_bytes(settings))
        atomic_write(state_path, json_bytes(state.payload()))

    return InstallResult(
        action=action,
        scope=scope,
        claude_root=str(root),
        runtime_root=str(runtime_root),
        files=len(file_hashes),
        hooks_enabled=enable_hooks,
        dry_run=dry_run,
    )


