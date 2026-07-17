# Economy Profile 0.3

Primary target: minimize total API-equivalent USD and startup overhead.

```text
minimum_savings_margin=0.40
max_active_workers=1
max_retries=0
max_worker_turns=6
allow_parallel_independent=false
allow_closed_context_batch=false
verification=independent_for_writes
```

Prefer `MAIN_DIRECT` for small, hot-context, or weakly calibrated tasks. Delegation must clear the USD gate; compression ratio alone is insufficient.
