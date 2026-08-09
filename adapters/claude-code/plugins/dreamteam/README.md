# DreamTeam Claude Code Plugin 0.5.0

The plugin installs disabled by default because it contributes enforcement hooks. Enable it explicitly after reviewing the project configuration.

Recommended first run:

```text
/dreamteam:init
/dreamteam:doctor
/dreamteam:run topology=lean profile=balanced <task>
```

Commands:

- `/dreamteam:init [--topology lean] [--profile balanced] [--strict] [--force]`
- `/dreamteam:doctor [--format json]`
- `/dreamteam:status [--run <run-id>] [--format json]`
- `/dreamteam:run topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>`
- `/dreamteam:review`
- `/dreamteam:measure <results.json>`

The plugin is self-contained. `lib/dreamteam` contains the canonical runtime; `scripts/` exposes routing, deterministic project operations, protocol, measurement, anchor, and hook entry points; and `hooks/hooks.json` applies project-root, budget, reread, nested-dispatch, and protected-config policy.

0.5 adds `routing_v05`, `measurement`, and `benchmark_v05`. Lean delegation accounts for root Sonnet executive overhead; cost, total-token, and main-token forecasts are reported separately; token gates remain shadow-only by default; and forecast routing never sets `empirical_claim_allowed=true`.

The catalog contains thirteen Haiku workers and three Sonnet roles. `opus-sonnet` is an explicit Opus executive → bounded Sonnet implementer path with a different Sonnet reviewer identity and no hidden Haiku component. Workers never spawn agents, and writing roles cannot accept their own changes.

Strict hooks reserve forecast cost. Authoritative provider usage is not yet available to the bundled adapter, so the reservation ledger is not a provider-side spending hard cap.
