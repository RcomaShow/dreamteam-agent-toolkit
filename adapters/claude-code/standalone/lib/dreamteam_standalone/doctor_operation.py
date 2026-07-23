"""Standalone adapter integrity diagnostics."""
from __future__ import annotations

from pathlib import Path

from .filesystem import (
    assert_state_targets,
    claude_root,
    load_state,
    read_json_object,
    safe_destination,
    validate_claude_root,
)
from .hooks import missing_hooks
from .model import (
    RUNTIME_RELATIVE_PATH,
    STATE_RELATIVE_PATH,
    Diagnostic,
    DoctorReport,
    StandaloneInstallError,
    digest,
)


def doctor(
    *,
    scope: str,
    project_root: str | Path | None = None,
    home: str | Path | None = None,
) -> DoctorReport:
    """Inspect a standalone installation without changing it."""
    root = claude_root(scope, project_root=project_root, home=home)
    validate_claude_root(root)
    state_path = safe_destination(root, STATE_RELATIVE_PATH)
    diagnostics: list[Diagnostic] = []
    try:
        state = load_state(state_path, required=True)
        assert state is not None
        assert_state_targets(state, root, scope)
    except (OSError, ValueError, StandaloneInstallError) as exc:
        diagnostics.append(Diagnostic("error", "STATE_UNAVAILABLE", str(exc)))
        return DoctorReport(
            ready=False,
            scope=None,
            claude_root=str(root),
            runtime_root=str(root / RUNTIME_RELATIVE_PATH),
            adapter_version=None,
            hooks_enabled=None,
            diagnostics=tuple(diagnostics),
        )

    for relative, expected in sorted(state.files.items()):
        try:
            target = safe_destination(root, Path(relative))
        except StandaloneInstallError as exc:
            diagnostics.append(Diagnostic("error", "TRACKED_PATH_INVALID", str(exc)))
            continue
        if not target.is_file() or target.is_symlink():
            diagnostics.append(
                Diagnostic("error", "FILE_MISSING", f"tracked file is missing: {relative}")
            )
            continue
        if digest(target.read_bytes()) != expected:
            diagnostics.append(
                Diagnostic("error", "FILE_MODIFIED", f"tracked file was modified: {relative}")
            )

    if state.hooks_enabled:
        try:
            settings = read_json_object(Path(state.settings_path), missing_ok=False)
            for event in missing_hooks(settings, state.expected_hooks):
                diagnostics.append(
                    Diagnostic("error", "HOOK_MISSING", f"tracked hook is missing: {event}")
                )
        except (OSError, ValueError, StandaloneInstallError) as exc:
            diagnostics.append(Diagnostic("error", "SETTINGS_UNAVAILABLE", str(exc)))
    else:
        diagnostics.append(
            Diagnostic("info", "HOOKS_NOT_INSTALLED", "standalone hooks were not requested")
        )

    if not any(item.severity == "error" for item in diagnostics):
        diagnostics.append(
            Diagnostic("info", "INSTALLATION_VALID", "standalone installation is consistent")
        )
    return DoctorReport(
        ready=not any(item.severity == "error" for item in diagnostics),
        scope=state.scope,
        claude_root=str(root),
        runtime_root=state.runtime_root,
        adapter_version=state.adapter_version,
        hooks_enabled=state.hooks_enabled,
        diagnostics=tuple(diagnostics),
    )


