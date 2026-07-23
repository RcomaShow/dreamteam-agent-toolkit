"""Safe removal of a tracked standalone adapter installation."""
from __future__ import annotations

from pathlib import Path

from .filesystem import (
    assert_state_targets,
    atomic_write,
    claude_root,
    load_state,
    prune_empty_directories,
    read_json_object,
    remove_files,
    safe_destination,
    validate_claude_root,
    verify_tracked_files,
)
from .hooks import missing_hooks, remove_related_hooks, remove_tracked_hooks
from .model import (
    RUNTIME_RELATIVE_PATH,
    STATE_RELATIVE_PATH,
    InstallResult,
    StandaloneInstallError,
    json_bytes,
)


def uninstall(
    *,
    scope: str,
    project_root: str | Path | None = None,
    home: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    """Remove only files and hooks tracked by the standalone adapter."""
    if type(force) is not bool or type(dry_run) is not bool:
        raise TypeError("force and dry_run must be booleans")
    root = claude_root(scope, project_root=project_root, home=home)
    validate_claude_root(root)
    state_path = safe_destination(root, STATE_RELATIVE_PATH)
    state = load_state(state_path, required=True)
    assert state is not None
    assert_state_targets(state, root, scope)
    verify_tracked_files(root, state.files, force=force)

    settings_path = Path(state.settings_path)
    settings: dict[str, object] = {}
    settings_changed = False
    if state.managed_hooks:
        settings = read_json_object(settings_path, missing_ok=True)
        missing = missing_hooks(settings, state.managed_hooks)
        if missing and not force:
            raise StandaloneInstallError(
                "tracked standalone hooks were modified or removed: " + ", ".join(missing)
            )
        if missing:
            settings_changed = remove_related_hooks(settings, Path(state.runtime_root))
        else:
            settings_changed = remove_tracked_hooks(settings, state.managed_hooks)

    if not dry_run:
        if settings_changed:
            if not state.settings_existed and not settings:
                settings_path.unlink(missing_ok=True)
            else:
                atomic_write(settings_path, json_bytes(settings))
        remove_files(root, state.files, force=force)
        state_path.unlink(missing_ok=True)
        prune_empty_directories(root / RUNTIME_RELATIVE_PATH, stop=root)
        prune_empty_directories(root / "skills", stop=root)
        prune_empty_directories(root / "agents", stop=root)

    return InstallResult(
        action="planned" if dry_run else "uninstalled",
        scope=scope,
        claude_root=str(root),
        runtime_root=state.runtime_root,
        files=len(state.files),
        hooks_enabled=state.hooks_enabled,
        dry_run=dry_run,
    )
