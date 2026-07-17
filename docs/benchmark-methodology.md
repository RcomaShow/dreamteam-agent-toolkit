# DreamTeam 0.4 Benchmark Methodology

Compare a pinned Sonnet direct arm against DreamTeam Lean, Opus-Sonnet, or Frontier on the same task, commit, oracle, config hash, environment, timeout, and cache cohort. Randomize arm order and preserve replicates.

Every run records adapter version, archetype, criticality, task kind, size band, concrete agent role, topology, route, model and effort usage, execution lane, cache operations, billed USD, API-equivalent USD, tokens, reread bytes, retries, escalations, failures, elapsed time, and pricing catalog. API-equivalent USD is recomputed from model usage, and aggregate token/cache counters must reconcile with the per-model records; mismatches invalidate the row.

Duplicate run IDs or arms, missing arms, unknown fields, string booleans, mismatched pair invariants, identical arm order, non-finite values, and zero direct cost invalidate economic claims.

Report median, mean, p10, negative-ROI pairs, quality parity, failures, latency, forecast error, and per-bucket distributions. Publication requires complete quality parity plus minimum samples, configured median margin, and positive p10 in every reported bucket.
