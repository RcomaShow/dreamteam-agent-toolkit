---
name: doctor
description: Inspect DreamTeam 0.4 runtime packaging, strict config invariants, topologies, hooks, agents, ledger charges, protocols, and validation readiness.
argument-hint: "[optional project path]"
disable-model-invocation: true
---

# DreamTeam Doctor 0.4

Inspect without changing configuration:

```text
PLUGIN_VERSION|0.4.0
RUNTIME_IMPORT|PASS|FAIL
CONFIG_VERSION|2
CONFIG_HASH|
PRICING_AS_OF|
PRICING_CATALOG_ID|
TOPOLOGY|lean|opus-sonnet|frontier
AGENT_COUNTS|haiku=13;sonnet=3
HOOKS|available|disabled-by-policy
LEDGER|off|sqlite
ENFORCEMENT|advisory|strict
RESERVATIONS|
CHARGED_USD_MICROS|
PROTOCOL_VALIDATOR|PASS|FAIL
BATCH_GATE|config;capability;closed_context;retention
MINIMUM_SAVINGS_MARGIN|
MAX_RUN_USD|
MAIN_REREAD_LIMIT|
STORE_SOURCE_CONTENT|false
SYNC_STATUS|
ARTIFACT_SMOKE_STATUS|
WARNINGS|
```

Strict mode is invalid unless telemetry is enabled, SQLite is active, hooks are available, the project-root config hash is stable, and all Agent dispatches use tool IDs and reservations. Check for outside-root paths, protected-config writes, self-review, hidden model stages, stale anchors, malformed handoffs, source-content persistence, symlinks, untracked release files, and unsupported model aliases.
