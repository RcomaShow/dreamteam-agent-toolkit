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
