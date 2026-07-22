---
name: doctor
description: Run deterministic DreamTeam 0.4.5 configuration, packaging, hook, agent-catalog, and strict-readiness diagnostics with actionable fixes.
argument-hint: "[--format json] [--plugin-data <path>]"
disable-model-invocation: true
---

# DreamTeam Doctor 0.4.5

Inspect without changing project configuration or ledger state:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_route.py" doctor --project-root "${CLAUDE_PROJECT_DIR}" --plugin-root "${CLAUDE_PLUGIN_ROOT}" --hooks-available $ARGUMENTS
```

The command returns stable text records or JSON. `STATUS|READY` means no blocking diagnostic was found. Every warning or error includes a stable issue code and a `FIX` record. Strict mode is ready only when telemetry is enabled, SQLite is configured, plugin data is writable, and Claude Code hooks are confirmed.
