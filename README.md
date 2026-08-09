# DreamTeam Agent Toolkit

[![validate](https://github.com/RcomaShow/dreamteam-agent-toolkit/actions/workflows/validate.yml/badge.svg)](https://github.com/RcomaShow/dreamteam-agent-toolkit/actions/workflows/validate.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The right agent for every task. Orchestrate smarter. Measure the result.**

DreamTeam 0.5.0 is a constitution-guided, measurement-first orchestration toolkit with a self-contained Claude Code plugin and a Codex-native adapter. It combines executable routing, project-root enforcement, compact DCP/2–CHP/2 handoffs, paired quality benchmarks, and separate accounting for cost, total tokens, root/main-model tokens, normalized payload, and handoff overhead.

## Five-minute Claude Code first run

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

## Codex adapter

Install the project instructions into a repository with an explicit non-overwriting installer:

```bash
python scripts/install_codex_adapter.py --scope project --project-root /path/to/project
```

Or install the optional DreamTeam user skill:

```bash
python scripts/install_codex_adapter.py --scope user
```

The Codex adapter uses the same constitution, criticality model, compact handoff discipline, and measurement contract without copying Claude-specific hook semantics or hardcoding transient provider model names.

## Topologies

```text
Lean:          Sonnet executive → Haiku bounded workers
Opus-Sonnet:   Opus executive → Sonnet bounded implementer + independent reviewer
Frontier:      Opus executive → Sonnet lead/reviewer → Haiku workers
```

Physical dispatch remains flat and owned by the root session. Workers cannot spawn workers. C3 and public-contract decisions stay executive-owned. A writing agent cannot be its own acceptance oracle.

In Opus-Sonnet, `execution-sonnet-lead` is the bounded implementation role; `verification-independent-reviewer` is a different agent identity. There is no hidden Haiku stage and no missing execution layer.

## What changed in 0.5

The 0.4 compatibility router remains available as `dreamteam.routing.choose_route`. Claude runs use the additive `dreamteam.routing_v05.choose_route_v05` path.

Lean delegation now requires an explicit root Sonnet executive usage forecast by default. The executive is priced as whole-tree overhead rather than implicitly treated as free. If that overhead removes the configured savings margin, 0.5 falls back to the direct baseline.

0.5 also separates these metrics:

- API-equivalent USD savings;
- total provider-token savings;
- root/main-model token savings;
- normalized payload/source-byte savings;
- handoff overhead;
- reread bytes, retries, escalations, failures, and latency;
- quality parity.

Token thresholds are reported in **shadow mode** by default. `--enforce-token-gates` is an explicit policy choice and should not be recommended until representative paired benchmarks calibrate the thresholds.

A cheaper model may support a cost-saving claim while still failing the token-efficiency claim.

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
- forecast run-budget gates for direct, delegated, and C3 routes;
- project-root path containment and protected configuration;
- exact-hash authorization for strict-mode Bash checks;
- metadata-only SQLite reservations, durable charges, checkpoints, and reread accounting;
- DCP/2 ledger registration and CHP/2 contract binding, source anchors, and independent reviewer identity;
- API-equivalent cost recomputation plus token-aware bucket publication gates;
- release archives built only from a clean, tracked Git tree with a source manifest and deterministic SBOM.

The Claude plugin installs disabled by default because it contributes enforcement hooks. No provider executor, network download, credential access, dependency installation, or paid inference is bundled.

### Budget boundary

The bundled strict hooks reserve forecast cost before Agent dispatch and commit that reservation on success. Although the ledger exposes reconciliation primitives, the plugin does not yet receive authoritative billed provider usage. Therefore the current budget is a hard gate on DreamTeam's forecast/accounting path, **not an authoritative provider-side spending cap**.

## Benchmark claims

`benchmark_v05` extends the paired 0.4 methodology and reports independent claim gates:

```text
cost_claim_allowed_v05
token_claim_allowed
payload_claim_allowed
efficiency_claim_allowed
```

A general efficiency claim requires equal-quality paired results plus publishable cost and token evidence in every reported bucket. Normalized payload measurements fail closed when the sidecar data is incomplete. Forecast routing always returns `empirical_claim_allowed=false`.

## Validate

```bash
make check
python scripts/measure.py
python scripts/build_release.py
python scripts/smoke_plugin_artifact.py dist/dreamteam-claude-code-plugin-0.5.0.zip
```

The expanded commands are documented in [`PUBLISHING.md`](PUBLISHING.md). The 0.5 architecture and claim boundaries are recorded in [`docs/v0.5-design.md`](docs/v0.5-design.md).

DreamTeam provides machinery to route and measure safely. It does not claim universal empirical savings until representative paired benchmarks pass every required quality, cost, token, and lower-tail gate.

## License

MIT
