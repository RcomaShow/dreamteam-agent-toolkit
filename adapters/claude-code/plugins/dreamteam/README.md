# DreamTeam Claude Code Plugin 0.2

Commands:

- `/dreamteam:run profile=<economy|balanced|offload|quality> <task>`
- `/dreamteam:review`
- `/dreamteam:measure`
- `/dreamteam:doctor`

DreamTeam 0.2 keeps the current session as final orchestrator and maps specialized workers to the `haiku` alias by default. The `offload` profile prioritizes reducing main-model work; C3 code remains orchestrator-owned.

Worker families:

- discovery: locator, tracer, pattern, impact, synthesis;
- execution: scaffold, mechanical, bounded logic, tests, documentation;
- verification: failure triage, diff audit, test gaps.

No Agent Teams, nested agents, hooks, MCP servers, or telemetry are enabled by default.
