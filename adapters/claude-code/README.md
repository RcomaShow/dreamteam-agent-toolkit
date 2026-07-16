# DreamTeam for Claude Code

This adapter packages the DreamTeam core as a Claude Code plugin and marketplace entry.

## Development

```bash
claude --plugin-dir ./adapters/claude-code/plugins/dreamteam
```

Inside Claude Code:

```text
/dreamteam:run profile=balanced <task>
/dreamteam:review
/dreamteam:measure
```

## Marketplace

The repository root contains `.claude-plugin/marketplace.json`, so after publishing:

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
```

## Model mapping

The default adapter maps specialized workers to the `haiku` alias and keeps the current main session as orchestrator. This mapping is adapter-specific; the DreamTeam core does not require a vendor or model family.

An environment-level Claude Code subagent override can supersede per-agent model fields. Check your Claude Code configuration if workers do not use the expected model.

## Safety

No hooks, MCP servers, monitors, or automatic commands are bundled. Write agents have narrow tool allowlists. Shell access is limited to test and failure roles and remains subject to Claude Code permissions.
