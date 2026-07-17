# DreamTeam Agent Toolkit

**The right agent for every task. Orchestrate smarter. Spend less.**

DreamTeam 0.3 is a constitution-guided, cost-proof orchestration toolkit with executable runtime enforcement and a self-contained Claude Code plugin.

## Topologies

```text
Lean:      Sonnet 5 executive → Haiku 4.5 bounded workers
Frontier:  Opus 4.8 executive → Sonnet 5 lead/reviewer → Haiku 4.5 workers
```

Physical dispatch remains flat. Workers cannot spawn workers. C3 and public-contract ownership stays with the executive, and a writer cannot be its own acceptance oracle.

## Cost-proof runtime

The bundled runtime provides strict configuration, reproducible pricing snapshots, whole-tree Lean/Frontier forecasts, Batch gating, exact reread accounting, SQLite checkpoints/budgets, source anchors, and fail-closed benchmark claims.

The direct baseline is always Sonnet 5-only. Frontier includes explicit Opus usage. Batch requires config opt-in, a real executor, closed context, and retention confirmation.

## Claude Code

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
/dreamteam:run topology=lean profile=balanced <task>
/dreamteam:review
/dreamteam:measure results.json
/dreamteam:doctor
```

The installable plugin contains the runtime under `lib/dreamteam`, executable scripts, 15 scoped agents, and advisory/strict hooks. No provider executor or paid inference is bundled.

## Validate

```bash
python scripts/sync_claude_adapter.py
git diff --exit-code
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/measure_v03.py
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.3.0.zip
```

Version 0.3 provides machinery to prove savings; it does not claim universal empirical savings until representative paired benchmarks pass the publication gate.

## License

MIT
