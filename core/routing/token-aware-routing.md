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
