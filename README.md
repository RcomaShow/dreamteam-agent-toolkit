# DreamTeam Agent Toolkit

[![validate](https://github.com/RcomaShow/dreamteam-agent-toolkit/actions/workflows/validate.yml/badge.svg)](https://github.com/RcomaShow/dreamteam-agent-toolkit/actions/workflows/validate.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The right agent for every task. Orchestrate smarter. Spend less.**

DreamTeam 0.4.2 is a constitution-guided orchestration toolkit and self-contained Claude Code plugin. It combines executable model routing, project-root enforcement, metadata-only cost accounting, bound DCP/2–CHP/2 handoffs, and claim-safe paired benchmarks.

## Five-minute first run

Install and enable the plugin:

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
/plugin enable dreamteam@dreamteam-tools
```

Create the recommended first-run configuration and inspect it:

```text
/dreamteam:init
/dreamteam:doctor
```

Then run a task:

```text
/dreamteam:run topology=lean profile=balanced <task>
```

The generated configuration uses the safe onboarding defaults:

```text
Topology:   lean
Profile:    balanced
Telemetry:  disabled
Ledger:     off
Enforcement: advisory
```

`/dreamteam:init` never silently overwrites an existing configuration. Use `--force` only after reviewing the replacement. Advanced strict enforcement is opt-in:

```text
/dreamteam:init --strict --force
/dreamteam:doctor
```

Strict mode requires SQLite telemetry and working Claude Code hooks. It is intended for audited runs, not as a prerequisite for trying the toolkit.

## Topologies

```text
Lean:          Sonnet 5 executive → Haiku 4.5 bounded workers
Opus-Sonnet:   Opus 4.8 executive → Sonnet 5 bounded implementer + independent reviewer
Frontier:      Opus 4.8 executive → Sonnet 5 lead/reviewer → Haiku 4.5 workers
```

Physical dispatch remains flat and owned by the root session. Workers cannot spawn workers. C3 and public-contract decisions stay executive-owned. A writing agent cannot be its own acceptance oracle.

In Opus-Sonnet, `execution-sonnet-lead` is the bounded implementation role; `verification-independent-reviewer` is a different agent identity. There is no hidden Haiku stage and no missing execution layer.

## Operational commands

```text
/dreamteam:init [--topology lean] [--profile balanced] [--strict] [--force]
/dreamteam:doctor [--format json]
/dreamteam:status [--run <run-id>] [--format json]
/dreamteam:run topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>
/dreamteam:review
/dreamteam:measure <results.json>
```

`status` reads only metadata from SQLite: charges, reservations, checkpoints, failed tool events, and invalidation categories. It does not reveal source content, prompts, raw commands, or credentials. When telemetry is disabled, it explains why no durable status exists.

The same deterministic project commands are available after Python installation:

```bash
python -m pip install -e .
dreamteam init --project-root .
dreamteam doctor --project-root .
dreamteam status --project-root . --run <run-id>
```

## What DreamTeam enforces

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

The plugin installs disabled by default because it contributes enforcement hooks. No provider executor, network download, credential access, dependency installation, or paid inference is bundled.

## Validate

```bash
make check
python scripts/measure.py
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.4.2.zip
```

The expanded commands are documented in [`PUBLISHING.md`](PUBLISHING.md). The implementation scope and architectural decisions for this release are recorded in [`docs/v0.4.1-implementation-plan.md`](docs/v0.4.1-implementation-plan.md).

DreamTeam provides machinery to route and measure safely. It does not claim universal empirical savings until representative paired benchmarks pass every quality and economic bucket gate.

## License

MIT
