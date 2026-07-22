#!/usr/bin/env python3
"""Generate the Claude Code adapter from platform-independent sources."""
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"
REF = PLUGIN / "skills/run/references"
LIB = PLUGIN / "lib/dreamteam"

AGENTS = {
    "discovery-symbol-locator": ("symbol-locator", "haiku", "low", "Read, Grep, Glob", 4),
    "discovery-flow-tracer": ("flow-tracer", "haiku", "medium", "Read, Grep, Glob", 10),
    "discovery-pattern-miner": ("pattern-miner", "haiku", "low", "Read, Grep, Glob", 7),
    "discovery-impact-mapper": ("impact-mapper", "haiku", "medium", "Read, Grep, Glob", 8),
    "discovery-context-synthesizer": ("context-synthesizer", "haiku", "low", "Read, Grep, Glob", 6),
    "execution-scaffold-builder": ("scaffold-builder", "haiku", "low", "Read, Grep, Glob, Edit, Write", 10),
    "execution-mechanical-editor": ("mechanical-editor", "haiku", "low", "Read, Grep, Glob, Edit, Write", 10),
    "execution-bounded-logic": ("bounded-logic-implementer", "haiku", "medium", "Read, Grep, Glob, Edit, Write, Bash", 10),
    "execution-test-writer": ("test-writer", "haiku", "medium", "Read, Grep, Glob, Edit, Write, Bash", 12),
    "execution-documentation-updater": ("documentation-updater", "haiku", "low", "Read, Grep, Glob, Edit, Write", 6),
    "execution-sonnet-lead": ("sonnet-lead", "sonnet", "high", "Read, Grep, Glob, Edit, Write, Bash", 12),
    "verification-failure-triage": ("failure-triage", "haiku", "medium", "Read, Grep, Glob, Bash", 8),
    "verification-diff-auditor": ("diff-auditor", "haiku", "medium", "Read, Grep, Glob, Bash", 8),
    "verification-test-gap-finder": ("test-gap-finder", "haiku", "low", "Read, Grep, Glob", 7),
    "coordination-decision-analyst": ("decision-analyst", "sonnet", "high", "Read, Grep, Glob", 8),
    "verification-independent-reviewer": ("independent-reviewer", "sonnet", "high", "Read, Grep, Glob, Bash", 10),
}

REFERENCE_MAPPING = {
    "constitution-kernel.md": ["core/constitution/kernel.md"],
    "routing-policy.md": [
        "core/routing/topologies.md",
        "core/routing/cost-proof-routing.md",
        "core/routing/code-criticality.md",
        "core/routing/escalation-policy.md",
    ],
    "compact-protocol.md": [
        "core/protocols/dcp-2.md",
        "core/protocols/chp-2.md",
        "core/protocols/escaping.md",
    ],
    "quality-gates.md": [
        "core/protocols/quality-gates.md",
        "core/routing/escalation-policy.md",
    ],
    "profiles.md": [
        "core/profiles/economy.md",
        "core/profiles/balanced.md",
        "core/profiles/offload.md",
        "core/profiles/quality.md",
    ],
}


def use_when(spec: str) -> str:
    return spec.split("## Use when", 1)[1].split("## Mission", 1)[0].strip().replace("\n", " ")


def generate_agent(name: str, worker: str, model: str, effort: str, tools: str, turns: int) -> str:
    spec = (ROOT / f"workers/{worker}/specification.md").read_text(encoding="utf-8")
    prompt = (ROOT / f"workers/{worker}/prompt.md").read_text(encoding="utf-8")
    return (
        f"---\nname: {name}\ndescription: {use_when(spec)}\nmodel: {model}\n"
        f"effort: {effort}\ntools: {tools}\nmaxTurns: {turns}\nbackground: false\n---\n\n"
        f"{prompt.rstrip()}\n\n## Claude Code handoff\n\n"
        "Do not call other agents or skills. Return DCP/2-compatible CHP/2 records within budget.\n"
    )


def copy_runtime() -> None:
    if LIB.exists():
        shutil.rmtree(LIB)
    LIB.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "dreamteam").glob("*.py")):
        shutil.copy2(source, LIB / source.name)
    typed_marker = ROOT / "dreamteam/py.typed"
    if typed_marker.is_file():
        shutil.copy2(typed_marker, LIB / typed_marker.name)


def generate_agents() -> None:
    agent_dir = PLUGIN / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    expected: set[str] = set()
    catalog = [
        "# DreamTeam 0.4.5 Worker Catalog",
        "",
        "| Agent | Model | Effort | Role |",
        "|---|---|---|---|",
    ]
    for name, values in AGENTS.items():
        worker, model, effort, tools, turns = values
        expected.add(f"{name}.md")
        (agent_dir / f"{name}.md").write_text(
            generate_agent(name, worker, model, effort, tools, turns),
            encoding="utf-8",
        )
        spec = (ROOT / f"workers/{worker}/specification.md").read_text(encoding="utf-8")
        catalog.append(f"| `{name}` | `{model}` | `{effort}` | {use_when(spec)} |")
    for stale in agent_dir.glob("*.md"):
        if stale.name not in expected:
            stale.unlink()
    catalog.extend(
        [
            "",
            "Select the narrowest role. Do not run agents with overlapping question and scope. The executive owns every dispatch and transition.",
        ]
    )
    REF.mkdir(parents=True, exist_ok=True)
    (REF / "worker-catalog.md").write_text("\n".join(catalog) + "\n", encoding="utf-8")


def generate_references() -> None:
    REF.mkdir(parents=True, exist_ok=True)
    for output, inputs in REFERENCE_MAPPING.items():
        content = "\n\n".join(
            (ROOT / item).read_text(encoding="utf-8").rstrip() for item in inputs
        ) + "\n"
        (REF / output).write_text(content, encoding="utf-8")


def main() -> int:
    copy_runtime()
    generate_agents()
    generate_references()
    print(
        f"generated {len(AGENTS)} agents, runtime library, and {len(REFERENCE_MAPPING) + 1} references"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
