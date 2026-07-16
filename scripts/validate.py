#!/usr/bin/env python3
"""Validate DreamTeam repository structure without external dependencies."""
from __future__ import annotations
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "adapters/claude-code/plugins/dreamteam"
ALLOWED_AGENT_FIELDS = {"name","description","model","effort","maxTurns","tools","disallowedTools","skills","memory","background","isolation"}
FORBIDDEN_PLUGIN_AGENT_FIELDS = {"hooks","mcpServers","permissionMode"}


def frontmatter(path: Path) -> dict[str,str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"): raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n",4)
    if end < 0: raise ValueError(f"{path}: unterminated YAML frontmatter")
    data = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        if ":" not in line: raise ValueError(f"{path}: unsupported frontmatter line: {line}")
        key,value=line.split(":",1); data[key.strip()]=value.strip()
    return data


def main() -> int:
    errors, warnings = [], []
    required = [
      ROOT/".claude-plugin/marketplace.json", PLUGIN/".claude-plugin/plugin.json",
      PLUGIN/"skills/run/SKILL.md", PLUGIN/"skills/doctor/SKILL.md",
      ROOT/"core/constitution/dreamteam-constitution.md", ROOT/"core/constitution/kernel.md",
      ROOT/"core/protocols/dcp-2.md", ROOT/"core/protocols/chp-2.md",
      ROOT/"core/profiles/offload.md", ROOT/"scripts/protocol_v2.py",
    ]
    for path in required:
        if not path.exists(): errors.append(f"missing: {path.relative_to(ROOT)}")
    try:
        market=json.loads((ROOT/".claude-plugin/marketplace.json").read_text())
        names=[p["name"] for p in market.get("plugins",[])]
        if len(names)!=len(set(names)): errors.append("duplicate marketplace plugin name")
        for entry in market.get("plugins",[]):
            source=entry.get("source","")
            if isinstance(source,str) and ".." in Path(source).parts: errors.append(f"marketplace source traverses parent: {source}")
            if not (ROOT/source).exists(): errors.append(f"missing marketplace source: {source}")
    except Exception as exc: errors.append(f"marketplace.json: {exc}")
    try:
        manifest=json.loads((PLUGIN/".claude-plugin/plugin.json").read_text())
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",manifest["name"]): errors.append("plugin name is not kebab-case")
        if manifest.get("version")!="0.2.0": warnings.append("plugin version is not 0.2.0")
    except Exception as exc: errors.append(f"plugin.json: {exc}")
    agent_names=set(); families=set()
    for path in sorted((PLUGIN/"agents").glob("*.md")):
        try:
            fm=frontmatter(path); name=fm.get("name",path.stem)
            if not fm.get("description"): errors.append(f"{path.name}: description required")
            if name in agent_names: errors.append(f"duplicate agent name: {name}")
            agent_names.add(name); families.add(name.split('-',1)[0])
            forbidden=FORBIDDEN_PLUGIN_AGENT_FIELDS.intersection(fm)
            if forbidden: errors.append(f"{path.name}: forbidden fields {sorted(forbidden)}")
            unknown=set(fm)-ALLOWED_AGENT_FIELDS-{"description"}
            if unknown: warnings.append(f"{path.name}: unknown fields {sorted(unknown)}")
            if fm.get("model")!="haiku": errors.append(f"{path.name}: worker model must be haiku")
            if "Agent" in [x.strip() for x in fm.get("tools","").split(',')]: errors.append(f"{path.name}: workers may not spawn workers")
            if "CHP/2" not in path.read_text(): errors.append(f"{path.name}: missing CHP/2 requirement")
        except Exception as exc: errors.append(str(exc))
    if families != {"discovery","execution","verification"}: errors.append(f"agent families mismatch: {sorted(families)}")
    if len(agent_names) < 10: errors.append("expected at least 10 specialized workers")
    for path in sorted((PLUGIN/"skills").glob("*/SKILL.md")):
        try:
            fm=frontmatter(path)
            if fm.get("disable-model-invocation")!="true": warnings.append(f"{path.relative_to(ROOT)} is model-invocable")
        except Exception as exc: errors.append(str(exc))
    for path in ROOT.rglob("*.md"):
        if "\t" in path.read_text(encoding="utf-8"): warnings.append(f"{path.relative_to(ROOT)} contains tabs")
        if path.stat().st_size>80_000: warnings.append(f"{path.relative_to(ROOT)} is large")
    print(f"Validated {len(list(ROOT.rglob('*')))} paths and {len(agent_names)} workers")
    for w in warnings: print(f"WARNING: {w}")
    for e in errors: print(f"ERROR: {e}",file=sys.stderr)
    return 1 if errors else 0

if __name__=="__main__": raise SystemExit(main())
