#!/usr/bin/env python3
"""Validate DreamTeam 0.4.2 repository, generated adapter, and security invariants."""
from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"
ALLOWED_AGENT_FIELDS = {
    "name", "description", "model", "effort", "maxTurns", "tools",
    "disallowedTools", "skills", "memory", "background", "isolation",
}
FORBIDDEN_AGENT_FIELDS = {"hooks", "mcpServers", "permissionMode"}
ALLOWED_EFFORT = {"low", "medium", "high", "xhigh", "max"}
EXPECTED_VERSION = "0.4.2"


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}: unsupported frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        ROOT / ".claude-plugin/marketplace.json",
        ROOT / "pyproject.toml",
        ROOT / "Makefile",
        ROOT / "dreamteam.config.minimal.json",
        ROOT / "docs/v0.4-implementation-plan.md",
        ROOT / "docs/v0.4.1-implementation-plan.md",
        ROOT / "docs/v0.4-stabilization-plan.md",
        PLUGIN / ".claude-plugin/plugin.json",
        PLUGIN / "hooks/hooks.json",
        PLUGIN / "scripts/dreamteam_init.py",
        PLUGIN / "scripts/dreamteam_route.py",
        PLUGIN / "scripts/dreamteam_measure.py",
        PLUGIN / "scripts/dreamteam_anchor.py",
        PLUGIN / "scripts/dreamteam_protocol.py",
        PLUGIN / "scripts/dreamteam_ledger_hook.py",
        PLUGIN / "lib/dreamteam/config.py",
        PLUGIN / "lib/dreamteam/routing.py",
        PLUGIN / "lib/dreamteam/protocol.py",
        PLUGIN / "lib/dreamteam/operations.py",
        PLUGIN / "lib/dreamteam/py.typed",
        PLUGIN / "skills/init/SKILL.md",
        PLUGIN / "skills/doctor/SKILL.md",
        PLUGIN / "skills/status/SKILL.md",
        PLUGIN / "skills/run/SKILL.md",
        PLUGIN / "skills/review/SKILL.md",
        ROOT / "core/schemas/dreamteam-config.schema.json",
        ROOT / "dreamteam/config.py",
        ROOT / "dreamteam/routing.py",
        ROOT / "dreamteam/protocol.py",
        ROOT / "dreamteam/ledger.py",
        ROOT / "dreamteam/anchors.py",
        ROOT / "dreamteam/benchmark.py",
        ROOT / "dreamteam/operations.py",
        ROOT / "dreamteam/py.typed",
        ROOT / "scripts/measure.py",
        ROOT / "scripts/smoke_plugin_artifact.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")
    for temporary in (
        ".dreamteam-bootstrap",
        ".dreamteam-tree-probe",
        ".github/workflows/export-source-temporary.yml",
        "scripts/bootstrap_v03.py",
        ".github/workflows/bootstrap-v03.yml",
        ".github/workflows/remediate-v03.yml",
    ):
        if (ROOT / temporary).exists():
            errors.append(f"temporary release file must not ship: {temporary}")

    try:
        manifest = json.loads(
            (PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
        )
        if manifest.get("version") != EXPECTED_VERSION:
            errors.append(f"plugin version must be {EXPECTED_VERSION}")
        if manifest.get("defaultEnabled") is not False:
            errors.append("plugin must require explicit enablement")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", manifest["name"]):
            errors.append("plugin name is not kebab-case")
    except Exception as exc:
        errors.append(f"plugin.json: {exc}")

    try:
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project = metadata["project"]
        if project.get("version") != EXPECTED_VERSION:
            errors.append(f"pyproject version must be {EXPECTED_VERSION}")
        if project.get("dependencies") != []:
            errors.append("runtime dependencies must remain empty")
        if project.get("requires-python") != ">=3.11":
            errors.append("requires-python must remain >=3.11")
    except Exception as exc:
        errors.append(f"pyproject.toml: {exc}")

    try:
        config = json.loads(
            (ROOT / "dreamteam.config.example.json").read_text(encoding="utf-8")
        )
        minimal = json.loads(
            (ROOT / "dreamteam.config.minimal.json").read_text(encoding="utf-8")
        )
        from dreamteam import __version__
        from dreamteam.config import RuntimeConfig, Topology
        from dreamteam.operations import minimal_config

        parsed = RuntimeConfig.from_mapping(config)
        RuntimeConfig.from_mapping(minimal)
        if __version__ != EXPECTED_VERSION:
            errors.append(f"runtime version must be {EXPECTED_VERSION}")
        if minimal != minimal_config():
            errors.append("dreamteam.config.minimal.json drifted from minimal_config()")
        if Topology.OPUS_SONNET.value != "opus-sonnet":
            errors.append("opus-sonnet topology is unavailable")
        if parsed.telemetry.enforcement == "strict" and not parsed.telemetry.enabled:
            errors.append("strict example config is not enabled")
    except Exception as exc:
        errors.append(f"configuration validation: {exc}")

    try:
        hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
        for event in (
            "PreToolUse", "PostToolUse", "PostToolUseFailure",
            "SubagentStart", "SubagentStop",
        ):
            if event not in hooks:
                errors.append(f"missing hook event: {event}")
        pre = json.dumps(hooks.get("PreToolUse", []))
        for tool in ("Read", "Grep", "Glob", "Edit", "Write", "Bash", "Agent"):
            if tool not in pre:
                errors.append(f"PreToolUse matcher missing {tool}")
    except Exception as exc:
        errors.append(f"hooks.json: {exc}")

    names: set[str] = set()
    families: set[str] = set()
    model_counts = {"haiku": 0, "sonnet": 0}
    for path in sorted((PLUGIN / "agents").glob("*.md")):
        try:
            fm = frontmatter(path)
            name = fm.get("name", path.stem)
            if name in names:
                errors.append(f"duplicate agent name: {name}")
            names.add(name)
            families.add(name.split("-", 1)[0])
            forbidden = FORBIDDEN_AGENT_FIELDS.intersection(fm)
            if forbidden:
                errors.append(f"{path.name}: forbidden fields {sorted(forbidden)}")
            unknown = set(fm) - ALLOWED_AGENT_FIELDS
            if unknown:
                warnings.append(f"{path.name}: unknown fields {sorted(unknown)}")
            model = fm.get("model")
            if model not in model_counts:
                errors.append(f"{path.name}: unsupported model {model}")
            else:
                model_counts[model] += 1
            if fm.get("effort") not in ALLOWED_EFFORT:
                errors.append(f"{path.name}: invalid or missing effort")
            if "Agent" in [item.strip() for item in fm.get("tools", "").split(",")]:
                errors.append(f"{path.name}: agents may not spawn agents")
            if "CHP/2" not in path.read_text(encoding="utf-8"):
                errors.append(f"{path.name}: missing CHP/2 requirement")
        except Exception as exc:
            errors.append(str(exc))
    if families != {"coordination", "discovery", "execution", "verification"}:
        errors.append(f"agent families mismatch: {sorted(families)}")
    if model_counts != {"haiku": 13, "sonnet": 3}:
        errors.append(f"model mapping mismatch: {model_counts}")
    if len(names) != 16:
        errors.append(f"expected 16 agents, found {len(names)}")
    if "execution-sonnet-lead" not in names:
        errors.append("missing execution-sonnet-lead")
    if "verification-independent-reviewer" not in names:
        errors.append("missing verification-independent-reviewer")

    try:
        hook_path = PLUGIN / "scripts/dreamteam_ledger_hook.py"
        spec = importlib.util.spec_from_file_location("dreamteam_validate_hook", hook_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load hook module")
        hook_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook_module)
        if set(hook_module.DREAMTEAM_AGENT_TYPES) != names:
            errors.append("hook agent-type registry does not match generated agents")
        for script_name in hook_module.TRUSTED_PLUGIN_SCRIPTS:
            if not (PLUGIN / "scripts" / script_name).is_file():
                errors.append(f"trusted plugin wrapper is missing: {script_name}")
        if "dreamteam_init.py" in hook_module.TRUSTED_PLUGIN_SCRIPTS:
            errors.append("mutating dreamteam_init.py must not bypass strict Bash authorization")
    except Exception as exc:
        errors.append(f"hook registry validation failed: {exc}")

    for module in (
        "dreamteam.pricing", "dreamteam.config", "dreamteam.routing",
        "dreamteam.anchors", "dreamteam.ledger", "dreamteam.protocol",
        "dreamteam.benchmark", "dreamteam.operations",
    ):
        try:
            importlib.import_module(module)
        except Exception as exc:
            errors.append(f"cannot import {module}: {exc}")

    for source in sorted((ROOT / "dreamteam").glob("*.py")):
        generated = PLUGIN / "lib/dreamteam" / source.name
        if not generated.exists() or generated.read_bytes() != source.read_bytes():
            errors.append(f"plugin runtime drift: {source.name}")
    typed_source = ROOT / "dreamteam/py.typed"
    typed_generated = PLUGIN / "lib/dreamteam/py.typed"
    if not typed_generated.exists() or typed_generated.read_bytes() != typed_source.read_bytes():
        errors.append("plugin runtime drift: py.typed")

    for skill in (PLUGIN / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        if "DreamTeam" in text and any(version in text for version in ("0.2", "0.3", "0.4\n")):
            errors.append(f"stale skill version: {skill.relative_to(ROOT)}")
    profiles = (PLUGIN / "skills/run/references/profiles.md").read_text(encoding="utf-8")
    if "Profile 0.4" not in profiles:
        errors.append("generated profiles reference is stale")
    routing = (PLUGIN / "skills/run/references/routing-policy.md").read_text(encoding="utf-8")
    if "Opus-Sonnet" not in routing:
        errors.append("generated routing reference lacks Opus-Sonnet")
    catalog = (PLUGIN / "skills/run/references/worker-catalog.md").read_text(encoding="utf-8")
    if not catalog.startswith("# DreamTeam 0.4.2 Worker Catalog\n"):
        errors.append("generated worker catalog version is stale")

    route_wrapper = (PLUGIN / "scripts/dreamteam_route.py").read_text(encoding="utf-8")
    if '"doctor", "status"' not in route_wrapper:
        errors.append("route wrapper does not expose read-only doctor/status operations")
    if '"init"' in route_wrapper.split("_OPERATION_COMMANDS", 1)[1].split("\n", 1)[0]:
        errors.append("route wrapper must not expose mutating init through the trusted wrapper")

    for template in (ROOT / "core/templates").glob("*.txt"):
        content = template.read_text(encoding="utf-8")
        if "CONTRACT|UNAVAILABLE" in content:
            errors.append(
                f"strict-incompatible template contract: {template.relative_to(ROOT)}"
            )

    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "\t" in text:
            warnings.append(f"{path.relative_to(ROOT)} contains tabs")
        if path.stat().st_size > 80_000:
            warnings.append(f"{path.relative_to(ROOT)} is large")

    print(f"Validated {len(list(ROOT.rglob('*')))} paths and {len(names)} agents")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
