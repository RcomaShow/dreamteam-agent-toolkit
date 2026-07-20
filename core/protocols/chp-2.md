# Compact Handoff Protocol — CHP/2

Workers return a decision-relevant delta, not a narrative recap.

```text
CHP|2
RUN|<run-id>
TASK|<task-id>
CONTRACT|<sha256>
S|<DONE|PARTIAL|BLOCKED|FAILED>|<short reason>
E|<id>|FACT|<source-anchor>|<claim>
E|<id>|DEDUCTION|<supporting ids>|<claim>
E|<id>|ASSUMPTION|<scope>|<claim>
E|<id>|UNKNOWN|<scope>|<claim>
C|<id>|<path#symbol>|<change>
H|<id>|<category>|<location>|<decision required>|<blocked work>
V|<id>|<PASS|FAIL|NR>|<check or command>|<result>
W|<id>|<risk>|<evidence>
N|<ORCHESTRATOR|WORKER:role>|<next action>
```

## Executable rules

- Strict mode rejects `CONTRACT|UNAVAILABLE`; `RUN`, `TASK`, and the hash must match a DCP/2 binding already registered in the run ledger.
- `FACT` requires a current source anchor when anchor validation is enabled.
- `DEDUCTION` cites existing evidence IDs.
- `DONE` cannot contain an unresolved `H` record.
- The writing agent and independent reviewer must have different agent IDs.
- The SubagentStop hook performs the same runtime validation automatically; `dreamteam_protocol.py` provides explicit preflight and ledger registration.
