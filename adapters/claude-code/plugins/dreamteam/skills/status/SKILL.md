---
name: status
description: Read a redacted DreamTeam 0.4.1 run summary from the metadata-only SQLite ledger.
argument-hint: "[--run <run-id>] [--format json]"
disable-model-invocation: true
---

# DreamTeam Status 0.4.1

Read durable metadata without exposing source content, prompts, raw commands, or credentials:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_route.py" status --project-root "${CLAUDE_PROJECT_DIR}" --plugin-data "${CLAUDE_PLUGIN_DATA}" $ARGUMENTS
```

The summary includes config hash, charged and reserved USD micros, active workers, checkpoint counts, failed tool events, and invalidation categories. When telemetry is disabled or no ledger exists, the command explains why status is unavailable and how to proceed.
