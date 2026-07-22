---
name: init
description: Create a validated DreamTeam 0.4.5 project configuration using safe advisory defaults or an explicit strict opt-in.
argument-hint: "[--topology lean] [--profile balanced] [--strict] [--force] [--format json]"
disable-model-invocation: true
---

# DreamTeam Init 0.4.5

Create `dreamteam.config.json` atomically in the stable Claude Code project root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_init.py" --project-root "${CLAUDE_PROJECT_DIR}" $ARGUMENTS
```

Without arguments, the command selects `lean`, `balanced`, telemetry disabled, ledger off, and advisory enforcement. It refuses to overwrite an existing file and rejects symlink targets. The init wrapper is intentionally not trusted by strict-mode Bash policy, so it cannot bypass protected-config immutability during an active strict run. Use `--strict` only after reviewing the generated configuration and use `--force` only for an intentional replacement.
