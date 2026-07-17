# DreamTeam 0.4 Topologies

The hierarchy is logical; physical dispatch is flat and owned by the root session. Hooks deny Agent dispatch from inside workers.

## Lean — Sonnet 5 → Haiku 4.5

Sonnet owns requirements, L2/C3 decisions, integration, independent writer review, and final acceptance. Haiku handles bounded discovery, M0 edits, completely specified L1 logic, tests, documentation, failure triage, and diff classification.

## Opus-Sonnet — Opus 4.8 → Sonnet 5

Opus owns planning, C3, public contracts, security, transaction, concurrency, idempotency, migrations, destructive behavior, and final acceptance. The bounded `execution-sonnet-lead` performs explicitly delegated L1/L2 implementation or integration and must hand authored changes to a different Sonnet reviewer. This topology contains no hidden Haiku stage.

## Frontier — Opus 4.8 → Sonnet 5 → Haiku 4.5

Opus owns cross-domain C3 decisions and final acceptance. Sonnet acts as bounded lead and independent reviewer. Haiku handles bounded volume. Frontier requires explicit Opus token forecast and is a quality route until paired benchmarks prove economic value for a task bucket.

## Routes

- `BLOCKED`: the request cannot proceed without violating a hard budget, strict runtime capability, or required ownership invariant.
- `MAIN_DIRECT`: localized, hot-context, ambiguous, uncalibrated, or economically superior work.
- `HAIKU_DISCOVERY`: bounded evidence gathering.
- `HAIKU_EXECUTE`: M0/L1 writing with a distinct Sonnet acceptance oracle.
- `SONNET_LEAD`: Opus-Sonnet execution, L2 integration, or independent review.
- `OPUS_DECISION`: C3 or cross-domain decision retained by the Opus executive.

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

# Code Criticality Classes

## M0 — Mechanical

DTOs, imports, renames, scaffolding, annotations, repeated edits, test skeletons, and documentation. Default owner: lower-cost worker.

## L1 — Bounded logic

Completely specified local transformations, mappings, parsing, validation, grouping, filtering, null rules, deterministic queries, and enumerated branches. Default owner: lower-cost bounded-logic worker.

## L2 — Mixed logic

Partially specified business behavior, multiple dependencies, ambiguous error handling, or legacy behavior requiring decisions. Default owner: hybrid; workers prepare and implement independent pieces, orchestrator owns unresolved logic.

## C3 — Consequential

Public contracts, security, transaction boundaries, concurrency, idempotency, Kafka acknowledgement/offset semantics, distributed consistency, database migrations, destructive operations, retry/compensation, and backward compatibility. Default owner: orchestrator.

File count never overrides criticality.

# Escalation Policy

Escalation means returning decision ownership, not silently choosing a stronger model.

Escalate when:

- a reserved decision is required;
- evidence conflicts;
- scope must expand;
- a public contract may change;
- security, transaction, concurrency, idempotency, or distributed consistency is involved;
- two bounded attempts fail on the same cause;
- required information is unavailable;
- verification contradicts the assumed behavior.

An escalation record includes location, evidence, decision required, blocked work, and recommended next owner.
