# DreamTeam for Claude Code 0.4.5

Development:

```bash
claude --plugin-dir ./adapters/claude-code/plugins/dreamteam
```

Marketplace:

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
/plugin enable dreamteam@dreamteam-tools
```

First run:

```text
/dreamteam:init
/dreamteam:doctor
/dreamteam:run topology=lean profile=balanced <task>
```

Operational commands:

```text
/dreamteam:init [--topology lean] [--profile balanced] [--strict] [--force]
/dreamteam:doctor [--format json]
/dreamteam:status [--run <run-id>] [--format json]
/dreamteam:run topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>
/dreamteam:review
/dreamteam:measure <results.json>
```

The plugin installs disabled by default because it contributes enforcement hooks. The root session remains the only physical dispatcher; thirteen Haiku workers and three Sonnet roles receive bounded contracts, while Opus is used by the executive session in `opus-sonnet` and `frontier` topologies. In Opus-Sonnet, the bounded implementer and independent reviewer are different Sonnet agent identities. Run `/dreamteam:doctor` before enabling strict telemetry.
