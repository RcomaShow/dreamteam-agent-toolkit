# Routing Policy 0.2

1. Classify code as M0, L1, L2, or C3.
2. Apply hard gates before considering delegation.
3. Select one of MAIN_DIRECT, WORKER_READ, WORKER_WRITE, HYBRID_EDIT, or HIGH_CAPABILITY_WORKER.
4. Use the shortest sufficient worker chain.
5. Declare a compact route packet before work begins.

## Hard gates for direct orchestrator ownership

- architecture or business semantics are undecided;
- public contracts, security, transaction, concurrency, idempotency, distributed consistency, database migration, or destructive behavior are involved;
- the task is localized and delegation overhead is comparable to implementation;
- the orchestrator must inspect almost all material anyway;
- acceptance criteria or a closed contract are missing.

## Delegation gates

Delegate read work when context volume is high and decision density is low. Delegate write work only when behavior, scope, editable symbols, reserved decisions, and verification are explicit.

Do not run overlapping workers on the same question. No worker delegates to another worker. The orchestrator owns every transition.

# Execution Routes

## MAIN_DIRECT

The orchestrator reads, decides, edits, and verifies. Use for localized but logically dense work, ambiguous semantics, high-risk changes, or when the delegation contract would be comparable to the implementation.

## WORKER_READ

A lower-cost read-only worker gathers evidence; the orchestrator decides and edits. Use for repository discovery, legacy tracing, impact analysis, pattern search, context compression, and failure diagnosis.

## WORKER_WRITE

A lower-cost worker edits fully specified M0 or L1 work; the orchestrator reviews proportionately to risk and runs final gates.

## HYBRID_EDIT

Workers handle discovery and mechanical/bounded implementation. The orchestrator owns L2/C3 regions and final review. This is the preferred path for mixed migration work.

## HIGH_CAPABILITY_WORKER

A separate high-capability worker isolates a difficult analysis or review. This route optimizes context isolation or quality, not model cost. It is disabled by default in `economy` and `offload`.

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

# Offload Policy

Optimization target: high-capability/main-model context and work.

Offload by default when a bounded worker can reliably perform:

- bulk repository search or symbol location;
- call-flow tracing and impact mapping;
- pattern comparison;
- context or log compression;
- scaffolding and repetitive edits;
- fully specified bounded logic;
- approved test implementation;
- failure triage, diff classification, and test-gap analysis.

The orchestrator retains:

- requirement interpretation and ambiguity resolution;
- architecture and business semantics;
- C3 code changes;
- public contracts and consequential error behavior;
- final ownership and quality gates.

## No duplicate work

The orchestrator verifies only decision-critical references, contradictions, consequential code, and required gates. It does not reproduce a worker investigation in full.

## Shortest sufficient chain

Use the minimum worker sequence. Return to the orchestrator whenever a decision is reached. Resume a compatible worker context instead of restarting when the runtime supports it.

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
