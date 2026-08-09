# DreamTeam for Claude Code 0.5.0

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

0.5 routes `/dreamteam:run` through measurement-first accounting: the Lean root Sonnet executive must be forecast explicitly before delegation, cost and token savings are reported separately, and token gates remain shadow-only unless explicitly enabled.

The plugin installs disabled by default because it contributes enforcement hooks. The root session remains the only physical dispatcher; thirteen Haiku workers and three Sonnet roles receive bounded contracts, while Opus is used by the executive session in `opus-sonnet` and `frontier` topologies. In Opus-Sonnet, the bounded implementer and independent reviewer are different Sonnet agent identities. Run `/dreamteam:doctor` before enabling strict telemetry.

Strict budget enforcement reserves forecast cost before Agent dispatch. Until authoritative provider usage is wired into reconciliation, this is not a provider-side hard spending cap.
