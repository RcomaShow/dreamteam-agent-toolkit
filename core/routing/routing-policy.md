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
