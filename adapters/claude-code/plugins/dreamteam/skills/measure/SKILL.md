---
name: measure
description: Summarize strict DreamTeam 0.5.0 paired benchmarks with independent cost, token, normalized-payload, cache, bucket, and quality claim gates.
argument-hint: "<results.json> [--normalized-measurements <measurements.json>]"
disable-model-invocation: true
---

# DreamTeam Measure 0.5.0

Use the same task, commit, oracle, config hash, environment, timeout, and cache cohort for both arms. Randomize arm order.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_measure.py" results.json
```

When normalized payload/source-byte measurements are available:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_measure.py" results.json --normalized-measurements measurements.json
```

Every benchmark row must include adapter version, config/environment identifiers, timeout, model usage, lane, cache operations, retries, escalations, failures, reread bytes, billed USD, and API-equivalent USD. The runtime recomputes API-equivalent USD from model usage and rejects mismatches.

0.5 reports `cost_claim_allowed_v05`, `token_claim_allowed`, `payload_claim_allowed`, and `efficiency_claim_allowed` separately. Token claims require total-token and main-token sample, median, and positive lower-tail gates. Payload claims fail closed when normalized measurements are incomplete. No provider executor is bundled.
