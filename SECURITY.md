# Security

Agent extensions can read files, execute commands, and modify repositories. Treat third-party prompts, plugins, skills, and scripts as executable supply-chain inputs.

## DreamTeam defaults

- Read-only workers receive no write tools.
- Write workers receive no shell tool unless targeted verification is part of their role.
- Workers cannot spawn other workers.
- Critical decisions are reserved to the orchestrator.
- Destructive commands, credential access, dependency installation, network downloads, and permission changes are never implicitly authorized.
- No hooks, MCP servers, background monitors, or automatic shell execution ship in `0.1.0`.

## Reporting

Do not open a public issue for a vulnerability that exposes secrets or enables destructive execution. Contact the repository owner privately through GitHub.
