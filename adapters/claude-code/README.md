# DreamTeam for Claude Code 0.4

Development:

```bash
claude --plugin-dir ./adapters/claude-code/plugins/dreamteam
```

Commands:

```text
/dreamteam:run topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>
/dreamteam:review
/dreamteam:measure <results.json>
/dreamteam:doctor
```

Marketplace:

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
/plugin enable dreamteam@dreamteam-tools
```

The plugin installs disabled by default because it contributes enforcement hooks. The root session remains the only physical dispatcher; thirteen Haiku workers and three Sonnet roles receive bounded contracts, while Opus is used by the executive session in `opus-sonnet` and `frontier` topologies. Run `/dreamteam:doctor` before enabling strict telemetry.
