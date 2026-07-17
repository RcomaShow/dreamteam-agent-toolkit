# Cost-Proof Routing 0.3

Delegation is an economic hypothesis. The direct baseline is always Sonnet 5-only with an explicit pricing snapshot and explicit cache usage; topology never changes the baseline.

## Whole-tree candidate

Account separately for Haiku worker, Sonnet lead, Sonnet independent verifier, Frontier Opus executive, cache reads/writes, Batch lane, expected retries, and expected escalation to the direct fallback.

Frontier is not a free quality tier: every candidate requires a non-zero Opus executive forecast. Missing executive usage fails closed to direct.

## Conservative gate

Delegate only when the candidate:

1. is permitted by criticality and independent verification;
2. stays below escalation, reread, run-budget, and calibration limits;
3. clears `minimumSavingsMargin` against the pinned direct baseline.

When rejected, preserve both the selected direct cost and the rejected candidate cost for audit.

## Batch

Batch is eligible only when the context is closed, retention is confirmed, project config opts in, and an actual Batch executor is available. Interactive Claude Code subagents are never priced as Batch.

## Calibration and claims

Enforcement is bucket-specific by role, archetype, criticality, size, effort, cache mode, and adapter version. No savings claim is valid without paired quality parity, positive median savings, representative samples, and a positive lower-tail result.
