# Token- and Cost-Aware Routing 0.4

Optimize and report separately:

```text
total_tokens
executive_tokens
worker_tokens
api_equivalent_usd
billed_usd
reread_bytes
latency
```

A delegated candidate includes instructions, context reconstruction, worker output, Sonnet lead/review, Opus executive usage where applicable, cache reads/writes, retries, and escalation to the direct fallback. The direct comparison remains a pinned Sonnet baseline.

Use blob-stable staged reads, source anchors, compact CHP/2 records, and decision-critical reread permits to avoid duplicated context. Calibration is bucket-specific; until sufficient paired samples exist, enforcement remains direct or shadow-only rather than assuming delegation is cheaper.
