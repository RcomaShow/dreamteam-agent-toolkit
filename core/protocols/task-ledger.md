# Task Ledger Protocol — TLP/1

The orchestrator maintains a compact state ledger across delegations.

```text
TASK|<id>|<owner>|<PENDING|ACTIVE|DONE|BLOCKED>|<scope>
DEC|<id>|<decision>|<evidence IDs>|<impact>
OPEN|<id>|<owner>|<required action>|<blocked task IDs>
CHK|<id>|<PASS|FAIL|NR>|<verification>
WORKER|<id>|<role>|<scope>|<ACTIVE|PAUSED|CLOSED>
```

## Rules

- Record only state needed for the next action.
- Replace stale records instead of appending duplicate prose.
- Reference handoff IDs instead of copying their content.
- Resume the same worker context when the runtime supports it and the scope is unchanged.
- Start a new worker when ownership, component, or goal changes.
