---
name: doctor
description: Inspect DreamTeam plugin version, configuration, model mappings, environment overrides, worker catalog, protocol version, and validation readiness.
argument-hint: "[optional project path]"
disable-model-invocation: true
---

# DreamTeam Doctor

Inspect without changing configuration:

```text
PLUGIN_VERSION|
CONSTITUTION|DT-C1
PROTOCOL|DCP/2,CHP/2
ACTIVE_PROFILE|
CONFIG_SOURCE|
MAIN_MODEL|
WORKER_MODEL_MAPPING|haiku
SUBAGENT_MODEL_OVERRIDE|
AVAILABLE_WORKERS|
OPTIONAL_HOOKS|disabled
VALIDATOR_STATUS|
WARNINGS|
```

Check for `dreamteam.config.json`, `CLAUDE_CODE_SUBAGENT_MODEL`, missing agents/references, invalid JSON, unsupported profile values, and unavailable targeted commands. Do not expose secrets or full environment values.
