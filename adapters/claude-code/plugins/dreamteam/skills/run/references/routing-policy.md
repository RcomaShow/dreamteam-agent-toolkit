# DreamTeam 0.3 Topologies

The hierarchy is logical; physical dispatch is flat and owned by the root session. Hooks deny Agent dispatch from inside workers.

## Lean — Sonnet 5 → Haiku 4.5

Sonnet owns requirements, L2/C3 decisions, integration, independent writer review, and final acceptance. Haiku handles bounded discovery, M0 edits, completely specified L1 logic, tests, documentation, failure triage, and diff classification.

## Frontier — Opus 4.8 → Sonnet 5 → Haiku 4.5

Opus owns cross-domain C3 decisions and final acceptance. Sonnet acts as bounded lead and independent reviewer. Haiku handles bounded volume. Frontier requires explicit Opus token forecast and is a quality route until paired benchmarks prove economic value for a task bucket.

## Routes

- `MAIN_DIRECT`: localized, hot-context, ambiguous, uncalibrated, over-budget, or consequential work.
- `HAIKU_DISCOVERY`: bounded evidence gathering.
- `HAIKU_EXECUTE`: M0/L1 writing with a distinct Sonnet acceptance oracle.
- `SONNET_LEAD`: L2 integration or independent review.
- `OPUS_DECISION`: Frontier C3 or cross-domain decision.

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
