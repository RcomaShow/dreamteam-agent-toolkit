# DreamTeam Agent Toolkit

**The right agent for every task. Orchestrate smarter. Spend less.**

DreamTeam 0.4 is a constitution-guided orchestration toolkit and self-contained Claude Code plugin. It combines executable model routing, strict project-root enforcement, durable cost accounting, bound DCP/2–CHP/2 handoffs, and claim-safe paired benchmarks.

## Topologies

```text
Lean:          Sonnet 5 executive → Haiku 4.5 bounded workers
Opus-Sonnet:   Opus 4.8 executive → Sonnet 5 lead/reviewer
Frontier:      Opus 4.8 executive → Sonnet 5 lead/reviewer → Haiku 4.5 workers
```

Physical dispatch remains flat and owned by the root session. Workers cannot spawn workers. C3 and public-contract decisions stay executive-owned, and a writer cannot be its own acceptance oracle.

## What 0.4 enforces

- strict JSON configuration and request parsing;
- executable `economy`, `balanced`, `offload`, and `quality` profiles;
- concrete agent-role and execution-chain selection;
- hard run budgets for direct, delegated, and C3 routes;
- project-root path containment and protected configuration;
- exact-hash authorization for strict-mode Bash checks;
- metadata-only SQLite reservations, durable charges, checkpoints, and reread accounting;
- DCP/2 ledger registration and CHP/2 contract binding, source anchors, and independent reviewer identity;
- API-equivalent cost recomputation and bucket-specific publication gates;
- release archives built only from a clean, tracked Git tree with a source manifest.

The plugin installs disabled by default because it contributes enforcement hooks. Enable it explicitly after reviewing `dreamteam.config.json`. No provider executor, network download, credential access, dependency installation, or paid inference is bundled.

## Claude Code

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
/plugin enable dreamteam@dreamteam-tools
/dreamteam:run topology=opus-sonnet profile=balanced <task>
/dreamteam:review
/dreamteam:measure results.json
/dreamteam:doctor
```

## Validate

```bash
python scripts/sync_claude_adapter.py
git diff --exit-code
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/measure.py
python -m compileall dreamteam adapters/claude-code/plugins/dreamteam
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.4.0.zip
```

Version 0.4 provides machinery to route and measure safely. It does not claim universal empirical savings until representative paired benchmarks pass every bucket gate.

## License

MIT
