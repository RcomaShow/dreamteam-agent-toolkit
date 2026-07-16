# Routing Policy

## Direct orchestrator work

Prefer direct work when:

- the task is one or two local files;
- delegation startup would exceed the likely exploration;
- the change is logically dense;
- decisions remain ambiguous;
- risk is high;
- the orchestrator must inspect almost all source material anyway.

## Delegate to a read-only worker

Use for:

- repository exploration across several files;
- finding definitions, callers, and analogues;
- summarizing large but bounded context;
- filtering verbose diagnostics;
- collecting evidence before a decision.

## Delegate to a write worker

Use only when:

- signatures and behavior are already decided;
- allowed files are closed;
- a clear pattern exists;
- work is mechanical or repetitive;
- the orchestrator will review the diff.

## Sequence

```text
classify -> contract -> delegate -> compact handoff ->
verify critical evidence -> decide -> optionally redelegate ->
final diff review -> required checks
```

Do not run multiple workers on the same question. Parallelize only independent scopes with no shared files or decisions.

# Complexity Model

Score each dimension from 0 to 2.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Volume `V` | 1–2 local files | 3–5 files or moderate log | 6+ files or large output |
| Repeatability `M` | novel | partly patterned | highly mechanical |
| Specification clarity `S` | ambiguous | some decisions fixed | closed contract |
| Logical complexity `C` | trivial | branching | distributed/concurrent/transactional |
| Risk `R` | reversible/local | public behavior | security/data/production |
| Delegation overhead `O` | high relative to task | moderate | low relative to task |

Suggested delegation signal:

```text
signal = V + M + S + O - C - R
```

Delegate when `signal >= 3` and no hard stop applies. This is an operational heuristic, not a token estimator.

## Hard stops for lower-capability workers

- business semantics not defined;
- public API/event contract design;
- security or authorization;
- data ownership or schema migration;
- transaction boundaries;
- idempotency, retry, compensation, or offset semantics;
- concurrency;
- destructive operations;
- dependency or build-system changes without explicit approval.

# Token-Aware Routing

Optimize both total tokens and high-cost-model tokens.

## Delegation condition

Delegate only when the expected material kept out of the orchestrator context is meaningfully larger than:

```text
worker instructions + context reconstruction + handoff + orchestrator verification
```

## Savings mechanisms

1. Use a narrow worker prompt.
2. Read only files that answer a concrete question.
3. Return record-based deltas, not narrative reports.
4. Cap deep reads, turns, output records, and retries.
5. Resume compatible worker contexts instead of restarting.
6. Do not make the orchestrator reread every worker-read file.
7. Verify only decision-critical evidence and the final diff.
8. Keep verbose logs outside the main context.
9. Avoid model switching in the main session when a separate worker can handle the lower-cost work.
10. Measure on representative tasks.

## Anti-patterns

- delegating a two-minute edit;
- starting several overlapping scouts;
- asking a worker to design and implement an ambiguous system;
- returning long code excerpts already available in the repository;
- making the orchestrator repeat the entire exploration;
- retry loops without a new hypothesis;
- loading all reference documents for every task.
