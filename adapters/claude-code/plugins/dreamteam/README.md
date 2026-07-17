# DreamTeam Claude Code Plugin 0.3

Commands:

- `/dreamteam:run topology=<lean|frontier> profile=<economy|balanced|offload|quality> <task>`
- `/dreamteam:review`
- `/dreamteam:measure`
- `/dreamteam:doctor`

The plugin is self-contained: `lib/dreamteam` holds the runtime, `scripts/` exposes routing/measurement/anchor/hook entry points, and `hooks/hooks.json` provides metadata-only enforcement.

There are thirteen Haiku workers, one Sonnet decision analyst, and one Sonnet independent reviewer. Workers never spawn agents. Hooks are advisory unless project config enables SQLite telemetry with strict enforcement.
