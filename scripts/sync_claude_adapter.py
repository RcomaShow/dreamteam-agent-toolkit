#!/usr/bin/env python3
"""Refresh Claude Code reference copies from the platform-independent core."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "adapters/claude-code/plugins/dreamteam/skills/run/references"

mapping = {
    "routing-policy.md": [
        "core/routing/routing-policy.md",
        "core/routing/complexity-model.md",
        "core/routing/token-aware-routing.md",
    ],
    "compact-protocol.md": [
        "core/protocols/delegation-contract.md",
        "core/protocols/compact-handoff.md",
        "core/protocols/task-ledger.md",
    ],
    "quality-gates.md": [
        "core/protocols/quality-gates.md",
        "core/routing/escalation-policy.md",
    ],
    "profiles.md": [
        "core/profiles/economy.md",
        "core/profiles/balanced.md",
        "core/profiles/quality.md",
    ],
}

for output, inputs in mapping.items():
    content = "\n\n".join((ROOT / item).read_text(encoding="utf-8").rstrip() for item in inputs) + "\n"
    (REF / output).write_text(content, encoding="utf-8")
    print(f"updated {REF / output}")
