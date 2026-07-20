# DreamTeam Operational Metrics

DreamTeam telemetry remains metadata-only. Every event should include `run_id`, `task_id`, `attempt_id`, `tool_use_id`, `agent_id`, `agent_role`, `model`, `topology`, `profile`, `criticality`, `task_kind`, `size_band`, `route`, `adapter_version`, `config_hash`, `repo_commit`, and `cache_cohort` where available.

## Cost and token metrics

- input, output, cache-read, cache-write-5m, and cache-write-1h tokens by model and phase;
- billed and API-equivalent USD;
- cost per successful task;
- forecast error ratio;
- reserved, charged, and remaining budget;
- budget denial and overrun counts.

## Quality and context metrics

- task and first-pass success rates;
- validator rejection and reviewer disagreement rates;
- output discard rate;
- unique bytes, reread bytes, reread ratio, manifest/cache hit rate;
- files and deep reads per task;
- handoff record and token counts;
- stale-anchor rate.

## Reliability and security metrics

- task, tool, and hook latency;
- retry, escalation, timeout, cancellation, loop, and partial-failure counts;
- stale checkpoints and reservations;
- outside-root attempts, protected-config writes, denied tools, malformed protocols, self-review attempts, secret redactions, release untracked-file count, and release symlink count.

Strict-mode release targets are zero unaccounted reads, zero stale reservations, zero outside-root access, zero self-review, zero untracked release files, and zero symlinks. Calibration and publication thresholds are evaluated per task bucket rather than globally.
