# DreamTeam Claude Code Plugin 0.4.5

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

The catalog contains thirteen Haiku workers and three Sonnet roles. `opus-sonnet` is an explicit Opus executive → bounded Sonnet implementer path with a different Sonnet reviewer identity and no hidden Haiku component. Workers never spawn agents, and writing roles cannot accept their own changes.
