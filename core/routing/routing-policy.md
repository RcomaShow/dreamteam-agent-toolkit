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
