# DreamTeam 0.3 Benchmark Methodology

Compare pinned Sonnet 5 direct against DreamTeam Lean or Frontier on the same commit, task, quality oracle, environment, and time limits. Randomize arm order and separate cold/warm-cache cohorts.

Each run records run/pair/replicate IDs, commit, archetype, topology, route, model usage and effort, cache cohort, arm order, oracle, strict boolean quality result, billed USD, API-equivalent USD, tokens, reread bytes, retries, escalations, failures, elapsed time, and pricing catalog.

Duplicate arms, missing arms, unknown fields, string booleans, mismatched oracle/commit/catalog, and zero direct cost invalidate economic claims.

Report median, mean, p10, negative-ROI pairs, failure rate, and per-archetype distributions. Distinguish quality, positive-direction, margin, and publication claims. Publication requires full quality parity, positive median, configured margin, minimum samples, and positive p10.
