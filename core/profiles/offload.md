# Offload Profile 0.3

Primary target: reduce executive tokens without violating the whole-tree USD gate.

```text
minimum_savings_margin=0.20
max_active_workers=2
max_retries=1
max_worker_turns=10
allow_parallel_independent=true
allow_closed_context_batch=false
verification=independent_for_writes
```

Offload broad discovery, logs, scaffolding, bounded logic, tests, and diff classification only when scopes are independent and budget reservations fit. C3 remains executive-owned.
