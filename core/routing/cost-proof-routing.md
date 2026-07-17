# Cost-Proof Routing 0.4

Delegation is an economic and quality hypothesis. The comparison baseline remains pinned Sonnet 5 direct so benchmark cohorts stay comparable across topologies.

## Whole-tree candidate

Account separately for every active component: Haiku worker, Sonnet lead, Sonnet independent verifier, Opus executive, cache reads/writes, Batch lane, expected retries, and expected escalation to the direct fallback. Configured model aliases are resolved by the runtime; accepted configuration is never decorative.

`opus-sonnet` requires non-zero Opus executive and Sonnet lead forecasts and rejects hidden Haiku usage. `frontier` requires non-zero Opus executive, Sonnet lead, and Haiku worker forecasts; omitting any tier invalidates the candidate.

## Conservative gate

Delegate only when the candidate:

1. is permitted by criticality and independent verification;
2. stays below escalation, reread, run-budget, and calibration limits;
3. has the runtime capabilities required by strict mode;
4. clears `minimumSavingsMargin` against the pinned direct baseline.

The run budget is a hard gate for direct, C3, and delegated routes. A route that cannot fit is `BLOCKED`; it is never silently executed over budget. Rejected candidates preserve their forecast for audit.

## Profiles

Profile defaults are executable. Explicit configuration values override a profile, while omitted routing and budget values inherit its preset.

## Batch

Batch is eligible only when context is closed, retention is confirmed, project config opts in, and a real Batch executor is available. Interactive subagents are never priced as Batch.

## Calibration and claims

Enforcement is bucket-specific by role, archetype, criticality, size, effort, cache mode, topology, and adapter version. Publication requires paired quality parity, recomputed API-equivalent cost, positive median and lower-tail savings, configured margin, and minimum samples in every reported bucket.
