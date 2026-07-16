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
