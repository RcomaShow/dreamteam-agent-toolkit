# Token and Work Optimization 0.5

DreamTeam 0.5 treats **cost efficiency, whole-tree token efficiency, and root/main-model token efficiency as different objectives**. A cheaper worker may reduce API-equivalent USD while increasing total provider tokens; that outcome is a cost win but a token-efficiency failure.

## Primary measurements

A run should distinguish:

- total provider input/output/cache tokens;
- root/main-model tokens;
- bounded worker tokens;
- normalized source/payload bytes;
- DCP/2 and CHP/2 handoff tokens;
- duplicate/reread bytes;
- retries, escalations, failed attempts, and latency;
- API-equivalent USD;
- quality parity against the paired direct baseline.

Normalized payload bytes are intentionally separate from provider token counts because different models or tokenizer revisions can encode the same source with different token totals.

## Routing

Lean whole-tree forecasts include the root executive overhead. Token gates start in shadow mode:

```text
minimum total-token savings = 5%
minimum main-token savings  = 15%
```

These are calibration seeds, not universal targets. They should be promoted to enforced routing policy only for task buckets where representative paired benchmarks demonstrate equal quality, sufficient samples, positive median savings, and positive lower-tail savings.

## Dominant waste pattern

The first optimization target remains duplicated work. Reads are staged at PreToolUse and committed only if the Git blob is unchanged at PostToolUse. The orchestrator should not reread a worker investigation unless evidence conflicts or a reserved decision requires direct inspection.

Compact CHP/2 handoffs preserve decision-relevant facts, deductions, unknowns, risks, changes, and verification evidence without replaying the complete investigation. Handoff overhead is measured explicitly so protocol verbosity cannot hide inside lower-cost worker usage.

## Next context-engineering layer

Blob, symbol, query, and repository-capsule caches remain evaluation-driven. Add each cache only when invalidation semantics are clear and paired measurements show that it reduces repeated payload without increasing stale-context failures or decision errors.
