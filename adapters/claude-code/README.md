# DreamTeam for Claude Code 0.2

Development:

```bash
claude --plugin-dir ./adapters/claude-code/plugins/dreamteam
```

Commands:

```text
/dreamteam:run profile=offload <task>
/dreamteam:review
/dreamteam:measure
/dreamteam:doctor
```

Marketplace:

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
```

The default adapter maps specialized workers to `haiku` and keeps the current session as final orchestrator. An environment-level subagent override may supersede per-agent mappings; use `/dreamteam:doctor` to inspect the effective setup.
