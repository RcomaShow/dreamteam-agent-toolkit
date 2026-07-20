# Security

Agent extensions can read files, execute commands, and modify repositories. Treat prompts, plugins, hooks, repository content, generated handoffs, benchmark inputs, and tool output as untrusted supply-chain inputs.

DreamTeam workers cannot spawn agents. C3, public contracts, security, transactions, concurrency, idempotency, distributed consistency, migrations, and destructive behavior remain executive-owned. A writing worker cannot be its own acceptance oracle.

## 0.4 boundaries

The plugin installs disabled by default because its hooks affect every matched tool call. Enable it explicitly only after reviewing the project configuration.

- The project root comes from the stable Claude Code project directory, not the current working directory.
- Strict mode requires enabled SQLite telemetry, available hooks, an immutable configuration hash, identifiable Agent tool calls, and budget reservations.
- Reads and writes must resolve to regular non-symlink files inside the project root; Git metadata and plugin-data paths remain outside the agent tool boundary.
- `dreamteam.config.json` is immutable during a run.
- Generic shell composition, dangerous executables, nested interpreters, and shell-based file reads are denied in strict mode. Bundled DreamTeam wrappers are allowlisted by resolved plugin path; every other Bash command requires its exact SHA-256 in `DREAMTEAM_ALLOWED_BASH_SHA256`. Inline exports do not grant permission.
- Ledger invalidations store categories and hashes, not raw source or full shell commands.
- A valid DCP/2 must be registered immutably in the ledger before dispatch. CHP/2 must match the registered run, task, contract hash, current anchors, and any distinct author/reviewer identities.
- Release archives are produced only from clean Git-tracked regular files and include commit/file manifests.

Batch is a separate opt-in API lane. No provider executor, network download, credential access, dependency installation, or paid inference is triggered automatically.

Report vulnerabilities privately to the repository owner with affected version, reproduction, impact, and the smallest safe mitigation. Do not place secrets in a public issue.
