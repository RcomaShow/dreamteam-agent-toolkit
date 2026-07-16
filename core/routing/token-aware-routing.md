# Token-Aware Routing 0.2

Optimize separately:

```text
total_tokens
main_model_tokens
weighted_cost
```

The `offload` profile prioritizes `main_model_tokens`. This may accept modest worker overhead when it prevents the high-capability model from bulk reading, raw-log processing, repetitive implementation, or routine verification.

## Expected delegation value

Delegate only when avoided main-model work is meaningfully larger than:

```text
worker instructions + context reconstruction + handoff + main verification
```

Track:

- compression ratio: material processed by worker / handoff size;
- main reread ratio: worker-read material reread by main / worker-read material;
- duplicate deep reads;
- worker and main turns;
- total and main-model usage;
- quality parity and retries.

Initial targets for delegable discovery tasks:

```text
compression_ratio >= 4.0
main_reread_ratio <= 0.35
```

These are evaluation targets, not runtime guarantees.
