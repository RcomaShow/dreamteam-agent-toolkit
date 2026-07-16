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

# Escalation Policy

A worker must hand control back when any condition applies:

- a reserved decision is reached;
- the contract is incomplete;
- evidence conflicts;
- a new file outside scope is necessary;
- a public behavior would change;
- two plausible options remain;
- the retry budget is exhausted;
- verification fails for a non-mechanical reason;
- the task crosses a hard-stop category.

Each handoff must include:

```text
H|id|category|location|exact decision|required dependent work
F|...|evidence supporting the handoff
N|ORCHESTRATOR|single next action
```

The worker should finish independent mechanical work before returning `PARTIAL`.
