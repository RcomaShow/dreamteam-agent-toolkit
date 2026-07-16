# Quality Gates

Use explicit states; avoid the ambiguous word `complete`.

```text
SCOPED       Contract and boundaries are explicit
IMPLEMENTED  Requested edits exist
COMPILED     Targeted compilation passed
TESTED       Targeted tests passed
REVIEWED     Orchestrator inspected the diff and decisions
VERIFIED     Required end-to-end or acceptance check passed
```

A worker may report only gates it actually performed. Final task success requires the gates defined by the orchestrator before delegation.

## Minimum gates by work type

| Work type | Minimum worker gate | Final orchestrator gate |
|---|---|---|
| Read-only exploration | Evidence references | Critical references reviewed |
| Boilerplate | Implemented | Compiled + reviewed |
| Mechanical edit | Implemented | Diff reviewed + targeted check |
| Test writing | Target test passed where authorized | Production behavior reviewed |
| Failure triage | Root cause confidence and evidence | Corrective change verified |
