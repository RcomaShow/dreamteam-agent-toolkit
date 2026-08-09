# DreamTeam 0.5 Benchmark Methodology

Compare a strong pinned direct arm against DreamTeam Lean, Opus-Sonnet, or Frontier on the same task, commit, oracle, config hash, environment, timeout, tools, and cache cohort. Randomize arm order and preserve replicates. The direct arm must be allowed to use the same efficient repository tools; DreamTeam is not benchmarked against a deliberately wasteful full-tree baseline.

Every run records adapter version, archetype, criticality, task kind, size band, concrete agent role, topology, route, model and effort usage, execution lane, cache operations, billed USD, API-equivalent USD, provider tokens, reread bytes, retries, escalations, failures, elapsed time, and pricing catalog. API-equivalent USD is recomputed from model usage, and aggregate token/cache counters must reconcile with the per-model records; mismatches invalidate the row.

Duplicate run IDs or arms, missing arms, unknown fields, string booleans, mismatched pair invariants, identical arm order, non-finite values, and zero direct cost invalidate economic claims.

## 0.5 efficiency dimensions

Cost and token efficiency are separate claims:

- `cost_claim_allowed_v05` — API-equivalent cost evidence;
- `token_claim_allowed` — whole-tree and root/main-model token evidence;
- `payload_claim_allowed` — normalized source/payload byte evidence;
- `efficiency_claim_allowed` — requires both publishable cost and token evidence.

Normalized payload bytes are supplied through a strict run-id sidecar because provider tokenizers may change across models. Missing sidecar data fails closed for payload claims rather than being reconstructed from provider token counts.

Handoff tokens are reported independently so protocol overhead cannot disappear inside a cheaper worker's token total.

## Publication gates

Report median, mean, p10, negative-ROI pairs, quality parity, failures, latency, rereads, token deltas, payload deltas, handoff overhead, and per-bucket distributions.

Cost publication keeps the 0.4 quality/sample/margin/lower-tail gates. Token publication additionally requires, per reported bucket:

1. complete quality parity;
2. minimum sample count;
3. configured median total-token savings;
4. positive p10 total-token savings;
5. configured median root/main-token savings;
6. positive p10 root/main-token savings.

Forecast routing never establishes empirical savings. Representative paired provider runs are required before a general claim or before shadow token thresholds are recommended for enforcement.
