# DreamTeam Claude Code Plugin 0.4

The plugin installs disabled by default because it contributes enforcement hooks. Enable it explicitly after reviewing the project configuration.

Commands:

- `/dreamteam:run topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>`
- `/dreamteam:review`
- `/dreamteam:measure <results.json>`
- `/dreamteam:doctor`

The plugin is self-contained. `lib/dreamteam` contains the canonical runtime; `scripts/` exposes routing, protocol, measurement, anchor, and hook entry points; and `hooks/hooks.json` applies project-root, budget, reread, nested-dispatch, and protected-config policy.

The catalog contains thirteen Haiku workers and three Sonnet roles. `opus-sonnet` is an explicit Opus executive → Sonnet lead/reviewer path with no hidden Haiku component. Workers never spawn agents, and writing roles require a different acceptance oracle.
