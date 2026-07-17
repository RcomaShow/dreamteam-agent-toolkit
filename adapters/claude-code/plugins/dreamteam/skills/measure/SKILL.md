---
name: measure
description: Summarize strict paired DreamTeam benchmarks with quality parity, API-equivalent and billed USD, replications, cache cohorts, and fail-closed claim decisions.
argument-hint: "<results.json>"
disable-model-invocation: true
---

# DreamTeam Measure 0.3

Use the same commit, task, oracle, environment, and time limits for both arms. Randomize arm order and separate cold/warm-cache cohorts.

Run the bundled non-spending command:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_measure.py" results.json
```

The complete execution tree must include executive, lead, workers, verifier, retries, escalations, failures, cache operations, reread bytes, and pricing catalog. Strings are not accepted as booleans. Duplicate arms and missing arms are errors.

A publication claim requires complete quality parity, positive median savings, configured margin, minimum samples, and a positive lower-tail result. No provider executor is bundled.
