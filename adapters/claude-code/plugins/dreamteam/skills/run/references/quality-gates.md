# Quality Gates

Use explicit states; never use the ambiguous word `complete` as a quality claim.

```text
SCOPED       Contract, ownership, and boundaries are explicit
IMPLEMENTED  Requested edits exist
COMPILED     Targeted compilation passed
TESTED       Targeted tests passed
REVIEWED     Orchestrator inspected consequential changes and decisions
VERIFIED     Required acceptance or end-to-end check passed
```

A worker reports only gates it actually performed. Final success requires the gates defined before delegation.

## Minimum final gates

| Work class | Worker ownership | Final orchestrator gate |
|---|---|---|
| M0 mechanical | Worker | Diff classification + targeted check |
| L1 bounded logic | Worker | Behavior review + targeted tests |
| L2 mixed logic | Hybrid | Direct review of critical regions + tests |
| C3 consequential | Orchestrator | Direct implementation/review + required checks |
| Read-only discovery | Worker | Decision-critical references reviewed |
| Failure triage | Worker | Corrective change verified |

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
