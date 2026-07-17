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

# Balanced Profile 0.3

Default conservative compromise between cost, main-model load, and confidence.

```text
minimum_savings_margin=0.30
max_active_workers=1
max_retries=1
max_worker_turns=10
allow_parallel_independent=false
allow_closed_context_batch=false
verification=independent_for_writes
```

Use Lean by default. Frontier requires explicit Opus forecast and a quality justification.

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

# Quality Profile 0.3

Primary target: risk reduction and decision quality. It is not automatically a savings route.

```text
minimum_savings_margin=0.00
max_active_workers=2
max_retries=2
max_worker_turns=14
allow_parallel_independent=true
allow_closed_context_batch=false
verification=expanded_independent
frontier=allowed_when_explicitly_justified
```

Report quality value and economic result separately. Frontier must include Opus in the whole-tree forecast and cannot support a savings claim unless paired benchmarks prove it.
