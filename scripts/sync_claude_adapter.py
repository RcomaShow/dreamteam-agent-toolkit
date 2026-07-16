#!/usr/bin/env python3
"""Generate Claude Code agent files and references from the platform-independent core."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"
REF = PLUGIN / "skills/run/references"

AGENTS = {
    "discovery-symbol-locator": ("symbol-locator", "Read, Grep, Glob", 4),
    "discovery-flow-tracer": ("flow-tracer", "Read, Grep, Glob", 10),
    "discovery-pattern-miner": ("pattern-miner", "Read, Grep, Glob", 7),
    "discovery-impact-mapper": ("impact-mapper", "Read, Grep, Glob", 8),
    "discovery-context-synthesizer": ("context-synthesizer", "Read, Grep, Glob", 6),
    "execution-scaffold-builder": ("scaffold-builder", "Read, Grep, Glob, Edit, Write", 10),
    "execution-mechanical-editor": ("mechanical-editor", "Read, Grep, Glob, Edit, Write", 10),
    "execution-bounded-logic": ("bounded-logic-implementer", "Read, Grep, Glob, Edit, Write, Bash", 10),
    "execution-test-writer": ("test-writer", "Read, Grep, Glob, Edit, Write, Bash", 12),
    "execution-documentation-updater": ("documentation-updater", "Read, Grep, Glob, Edit, Write", 6),
    "verification-failure-triage": ("failure-triage", "Read, Grep, Glob, Bash", 8),
    "verification-diff-auditor": ("diff-auditor", "Read, Grep, Glob, Bash", 8),
    "verification-test-gap-finder": ("test-gap-finder", "Read, Grep, Glob", 7),
}

for old in (PLUGIN / "agents").glob("*.md"):
    old.unlink()
for filename, (worker, tools, turns) in AGENTS.items():
    spec = (ROOT / f"workers/{worker}/specification.md").read_text(encoding="utf-8")
    prompt = (ROOT / f"workers/{worker}/prompt.md").read_text(encoding="utf-8")
    description = next(line for line in spec.splitlines() if line.startswith("Default capability") or line.startswith("## Use when")) if False else ""
    use_when = spec.split("## Use when",1)[1].split("## Mission",1)[0].strip().replace("\n", " ")
    content = f"""---\nname: {filename}\ndescription: {use_when}\nmodel: haiku\ntools: {tools}\nmaxTurns: {turns}\nbackground: false\n---\n\n{prompt.rstrip()}\n\n## Claude Code handoff\n\nDo not call other agents or skills. Return DCP/2-compatible CHP/2 records within budget.\n"""
    (PLUGIN / "agents" / f"{filename}.md").write_text(content, encoding="utf-8")

mapping = {
    "constitution-kernel.md": ["core/constitution/kernel.md"],
    "routing-policy.md": ["core/routing/routing-policy.md", "core/routing/execution-routes.md", "core/routing/code-criticality.md", "core/routing/offload-policy.md", "core/routing/token-aware-routing.md"],
    "compact-protocol.md": ["core/protocols/dcp-2.md", "core/protocols/chp-2.md", "core/protocols/escaping.md"],
    "quality-gates.md": ["core/protocols/quality-gates.md", "core/routing/escalation-policy.md"],
    "profiles.md": ["core/profiles/economy.md", "core/profiles/balanced.md", "core/profiles/offload.md", "core/profiles/quality.md"],
    "worker-catalog.md": [str(p.relative_to(ROOT)) for p in sorted((ROOT / "workers").glob("*/specification.md"))],
}
for output, inputs in mapping.items():
    content = "\n\n".join((ROOT / item).read_text(encoding="utf-8").rstrip() for item in inputs) + "\n"
    (REF / output).write_text(content, encoding="utf-8")
    print(f"updated {REF / output}")
