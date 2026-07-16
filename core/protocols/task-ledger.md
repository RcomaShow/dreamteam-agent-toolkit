# Task Ledger Protocol — TLP/2

The orchestrator maintains compact mutable state across delegations.

```text
TLP|2
RUN|<run-id>
TASK|<id>|<owner>|<PENDING|ACTIVE|DONE|BLOCKED>|<scope>
ROUTE|<task-id>|<route>|<M0|L1|L2|C3>|<reason>
DEC|<id>|<decision>|<evidence IDs>|<impact>
OPEN|<id>|<owner>|<required action>|<blocked task IDs>
CHK|<id>|<PASS|FAIL|NR>|<verification>
WORKER|<id>|<role>|<scope>|<ACTIVE|PAUSED|CLOSED>
READ|<owner>|<reference>|<DEEP|SHALLOW>
```

## Rules

- Record only state required by the next action.
- Replace stale records instead of appending narrative history.
- Reference CHP/2 IDs instead of copying their content.
- Track deep reads to detect duplicated investigation.
- Resume the same worker context when scope and goal are unchanged and the runtime supports it.
- Start a new worker when ownership, component, or goal changes.
