# Economy Profile 0.4

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

These values are runtime defaults, not documentation-only suggestions. Prefer `MAIN_DIRECT` for small, hot-context, or weakly calibrated work.

# Balanced Profile 0.4

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

Use Lean by default. Use Opus-Sonnet when the Opus executive can transfer a bounded L1/L2 implementation to Sonnet without most of its reasoning context. Frontier requires explicit Opus, Sonnet, and Haiku accounting.

# Offload Profile 0.4

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

Offload broad discovery, logs, scaffolding, bounded logic, tests, diff classification, and bounded Opus-to-Sonnet implementation only when scopes are independent and budget reservations fit. C3 remains executive-owned.

# Quality Profile 0.4

Primary target: risk reduction and decision quality. It is not automatically a savings route.

```text
minimum_savings_margin=0.00
max_active_workers=2
max_retries=2
max_worker_turns=14
allow_parallel_independent=true
allow_closed_context_batch=false
verification=expanded_independent
opus_sonnet=allowed_when_explicitly_justified
frontier=allowed_when_explicitly_justified
```

Report quality value and economic result separately. Opus-Sonnet and Frontier include every active tier and cannot support a savings claim without paired benchmark evidence.
