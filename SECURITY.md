# Security

Agent extensions can read files, execute commands, and modify repositories. Treat prompts, plugins, hooks, repository content, generated handoffs, and benchmark inputs as supply-chain inputs.

DreamTeam workers cannot spawn agents. C3, public contracts, security, transactions, concurrency, idempotency, distributed consistency, migrations, and destructive behavior remain executive-owned. A writing worker cannot be its own acceptance oracle.

Plugin hooks store metadata only in `${CLAUDE_PLUGIN_DATA}`. Configuration requires `storeSourceContent=false`. Advisory mode avoids surprising blocks; strict benchmark mode fails closed on unaccountable reads, stale anchors, nested dispatch, and missing budget reservations.

Batch is a separate opt-in API lane. No provider executor, network download, credential access, dependency installation, or paid inference is triggered automatically.

Report vulnerabilities privately to the repository owner with affected version, reproduction, impact, and the smallest safe mitigation.
