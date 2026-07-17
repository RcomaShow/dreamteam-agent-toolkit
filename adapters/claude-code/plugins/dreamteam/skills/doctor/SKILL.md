---
name: doctor
description: Inspect DreamTeam 0.3 runtime packaging, config, pricing snapshot, hooks, agents, budget gates, telemetry, and validation readiness.
argument-hint: "[optional project path]"
disable-model-invocation: true
---

# DreamTeam Doctor 0.3

Inspect without changing configuration:

```text
PLUGIN_VERSION|0.3.0
RUNTIME_IMPORT|PASS|FAIL
CONFIG_VERSION|2
PRICING_AS_OF|
PRICING_CATALOG_ID|
TOPOLOGY|lean|frontier
AGENT_COUNTS|haiku=13;sonnet=2
HOOKS|available|disabled-by-policy
LEDGER|off|sqlite
ENFORCEMENT|advisory|strict
BATCH_GATE|config;capability;closed_context;retention
MINIMUM_SAVINGS_MARGIN|
MAX_RUN_USD|
MAIN_REREAD_LIMIT|
STORE_SOURCE_CONTENT|false
SYNC_STATUS|
ARTIFACT_SMOKE_STATUS|
WARNINGS|
```

Check for unsupported config, missing pricing snapshot, stale anchors, self-review, unreserved Agent dispatch, broad worker overlap, source-content persistence, missing plugin runtime, and model overrides. Do not expose secrets.
