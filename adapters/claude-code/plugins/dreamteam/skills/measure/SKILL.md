---
name: measure
description: Summarize strict DreamTeam 0.4.5 paired benchmarks with recomputed costs, pair invariants, cache cohorts, bucket gates, and fail-closed claims.
argument-hint: "<results.json>"
disable-model-invocation: true
---

# DreamTeam Measure 0.4.5

Use the same task, commit, oracle, config hash, environment, timeout, and cache cohort for both arms. Randomize arm order.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_measure.py" results.json
```

Every row must include adapter version, config/environment identifiers, timeout, model usage, lane, cache operations, retries, escalations, failures, reread bytes, billed USD, and API-equivalent USD. The runtime recomputes API-equivalent USD from model usage and rejects mismatches.

Publication requires complete quality parity plus sample, margin, and positive lower-tail gates in every reported task bucket. No provider executor is bundled.
