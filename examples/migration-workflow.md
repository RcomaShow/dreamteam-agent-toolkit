# Migration Workflow

1. `discovery-symbol-locator` identifies legacy entry points.
2. `discovery-flow-tracer` maps state, calls, and side effects.
3. `discovery-impact-mapper` bounds callers, contracts, tests, persistence, and configuration.
4. The orchestrator chooses service boundaries, contracts, transactions, idempotency, and migration strategy.
5. `execution-scaffold-builder` creates approved structures.
6. `execution-bounded-logic` implements fully specified local transformations.
7. The orchestrator edits C3 regions.
8. `execution-test-writer` implements approved cases.
9. `verification-diff-auditor` reduces final review to consequential regions.
10. The orchestrator runs final gates.
