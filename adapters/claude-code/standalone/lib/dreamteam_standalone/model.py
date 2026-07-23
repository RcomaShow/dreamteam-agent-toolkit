"""Data models and shared constants for the standalone adapter."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

ADAPTER_ID = "claude-code-standalone"
STATE_SCHEMA_VERSION = 1
STATE_RELATIVE_PATH = Path("dreamteam/install-state.json")
RUNTIME_RELATIVE_PATH = Path("dreamteam")
PLUGIN_ROOT_TOKEN = "${CLAUDE_PLUGIN_ROOT}"
COMMAND_NAMES = ("init", "doctor", "status", "run", "review", "measure")
REQUIRED_PLUGIN_PATHS = (
    Path(".claude-plugin/plugin.json"),
    Path("agents"),
    Path("hooks/hooks.json"),
    Path("lib"),
    Path("scripts"),
    Path("skills"),
)


class StandaloneInstallError(RuntimeError):
    """Raised when a standalone operation cannot be completed safely."""


@dataclass(frozen=True)
class InstallResult:
    action: str
    scope: str
    claude_root: str
    runtime_root: str
    files: int
    hooks_enabled: bool
    dry_run: bool

    def payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str

    def payload(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorReport:
    ready: bool
    scope: str | None
    claude_root: str
    runtime_root: str
    adapter_version: str | None
    hooks_enabled: bool | None
    diagnostics: tuple[Diagnostic, ...]

    def payload(self) -> dict[str, object]:
        data = asdict(self)
        data["diagnostics"] = [item.payload() for item in self.diagnostics]
        return data


@dataclass(frozen=True)
class InstallState:
    schema_version: int
    adapter: str
    adapter_version: str
    scope: str
    claude_root: str
    runtime_root: str
    settings_path: str
    settings_existed: bool
    hooks_enabled: bool
    files: dict[str, str]
    expected_hooks: dict[str, list[dict[str, object]]]
    managed_hooks: dict[str, list[dict[str, object]]]

    def payload(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "adapter": self.adapter,
            "adapterVersion": self.adapter_version,
            "scope": self.scope,
            "claudeRoot": self.claude_root,
            "runtimeRoot": self.runtime_root,
            "settingsPath": self.settings_path,
            "settingsExisted": self.settings_existed,
            "hooksEnabled": self.hooks_enabled,
            "files": dict(sorted(self.files.items())),
            "expectedHooks": self.expected_hooks,
            "managedHooks": self.managed_hooks,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "InstallState":
        schema_version = data.get("schemaVersion")
        adapter = data.get("adapter")
        adapter_version = data.get("adapterVersion")
        scope = data.get("scope")
        claude_root = data.get("claudeRoot")
        runtime_root = data.get("runtimeRoot")
        settings_path = data.get("settingsPath")
        settings_existed = data.get("settingsExisted")
        hooks_enabled = data.get("hooksEnabled")
        raw_files = data.get("files")
        raw_expected_hooks = data.get("expectedHooks")
        raw_managed_hooks = data.get("managedHooks")
        if schema_version != STATE_SCHEMA_VERSION:
            raise StandaloneInstallError("unsupported standalone install-state schema")
        if adapter != ADAPTER_ID:
            raise StandaloneInstallError("install-state belongs to a different adapter")
        for name, value in (
            ("adapterVersion", adapter_version),
            ("scope", scope),
            ("claudeRoot", claude_root),
            ("runtimeRoot", runtime_root),
            ("settingsPath", settings_path),
        ):
            if not isinstance(value, str) or not value:
                raise StandaloneInstallError(f"invalid install-state field: {name}")
        if scope not in {"project", "user"}:
            raise StandaloneInstallError("invalid standalone install scope")
        if type(settings_existed) is not bool or type(hooks_enabled) is not bool:
            raise StandaloneInstallError("invalid standalone install-state flags")
        if (
            not isinstance(raw_files, dict)
            or not isinstance(raw_expected_hooks, dict)
            or not isinstance(raw_managed_hooks, dict)
        ):
            raise StandaloneInstallError("invalid standalone install-state collections")
        files: dict[str, str] = {}
        for path, digest in raw_files.items():
            if not isinstance(path, str) or not isinstance(digest, str):
                raise StandaloneInstallError("invalid tracked file entry")
            files[path] = digest
        expected_hooks = normalize_hooks(raw_expected_hooks, "expected hook")
        managed_hooks = normalize_hooks(raw_managed_hooks, "managed hook")
        assert isinstance(adapter_version, str)
        assert isinstance(scope, str)
        assert isinstance(claude_root, str)
        assert isinstance(runtime_root, str)
        assert isinstance(settings_path, str)
        assert isinstance(settings_existed, bool)
        assert isinstance(hooks_enabled, bool)
        return cls(
            schema_version=STATE_SCHEMA_VERSION,
            adapter=ADAPTER_ID,
            adapter_version=adapter_version,
            scope=scope,
            claude_root=claude_root,
            runtime_root=runtime_root,
            settings_path=settings_path,
            settings_existed=settings_existed,
            hooks_enabled=hooks_enabled,
            files=files,
            expected_hooks=expected_hooks,
            managed_hooks=managed_hooks,
        )


def normalize_hooks(
    raw_hooks: Mapping[object, object],
    label: str,
) -> dict[str, list[dict[str, object]]]:
    hooks: dict[str, list[dict[str, object]]] = {}
    for event, entries in raw_hooks.items():
        if not isinstance(event, str) or not isinstance(entries, list):
            raise StandaloneInstallError(f"invalid {label} entry")
        normalized: list[dict[str, object]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise StandaloneInstallError(f"invalid {label} object")
            normalized.append(string_key_mapping(entry, label))
        hooks[event] = normalized
    return hooks


def string_key_mapping(value: Mapping[object, object], label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise StandaloneInstallError(f"{label} contains a non-string key")
        result[key] = item
    return result


def json_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def digest(content: bytes) -> str:
    return sha256(content).hexdigest()
