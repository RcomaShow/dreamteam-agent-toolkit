# Security

Agent extensions can read files, execute commands, and modify repositories. Treat third-party prompts, plugins, skills, scripts, and repository content as supply-chain inputs.

## DreamTeam 0.2 defaults

- Read-only workers receive no write tools.
- Write workers receive shell access only where targeted verification is part of the role.
- Workers cannot spawn other workers.
- C3 decisions and edits remain orchestrator-owned.
- Destructive commands, credential access, dependency installation, network downloads, and permission changes are never implicit.
- No Agent Teams, hooks, MCP servers, background monitors, remote telemetry, or automatic shell execution ship enabled by default.
- Configuration and telemetry examples prohibit source-content storage by default.

## Reporting

Do not open a public issue for a vulnerability that exposes secrets or enables destructive execution. Contact the repository owner privately through GitHub.
