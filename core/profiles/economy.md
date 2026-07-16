# Economy Profile

Primary target: minimize total usage and delegation overhead.

```text
optimization_target=total_tokens
max_active_workers=1
max_worker_chain=1
max_worker_turns=6
max_deep_reads=6
max_output_records=16
max_retries=1
parallelism=off
orchestrator_verification=critical_evidence_diff_and_targeted_checks
```

Prefer MAIN_DIRECT for small tasks and a single worker only for clearly beneficial work.
