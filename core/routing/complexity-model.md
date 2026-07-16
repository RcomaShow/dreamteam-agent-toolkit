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
