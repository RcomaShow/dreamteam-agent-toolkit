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
