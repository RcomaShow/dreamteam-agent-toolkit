# Compact Handoff Protocol — CHP/2

Workers return a decision-relevant delta, not a narrative recap.

```text
CHP|2
RUN|<run-id>
TASK|<task-id>
CONTRACT|<sha256 or UNAVAILABLE>
S|<DONE|PARTIAL|BLOCKED|FAILED>|<short reason>
E|<id>|FACT|<source>|<claim>
E|<id>|DEDUCTION|<supporting ids>|<claim>
E|<id>|ASSUMPTION|<scope>|<claim>
E|<id>|UNKNOWN|<scope>|<claim>
C|<id>|<path#symbol>|<change>
H|<id>|<category>|<location>|<decision required>|<blocked work>
V|<id>|<PASS|FAIL|NR>|<check or command>|<result>
W|<id>|<risk>|<evidence>
N|<ORCHESTRATOR|WORKER:role>|<next action>
```

## Precision rules

- `FACT` requires direct evidence.
- `DEDUCTION` cites existing evidence IDs.
- `ASSUMPTION` is allowed only when the contract permits it.
- `UNKNOWN` never silently becomes a fact.
- `DONE` means the worker contract is complete, not that the whole task is production-ready.
- `DONE` must not contain unresolved `H` records.
- `PASS` names the actual check; `NR` means not run.
- Do not repeat the contract, user request, or previously acknowledged records.
- Escape fields according to `escaping.md`.
