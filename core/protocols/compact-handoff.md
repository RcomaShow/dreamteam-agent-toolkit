# Compact Handoff Protocol — CHP/1

Workers return a delta, not a narrative recap.

```text
S|<DONE|PARTIAL|BLOCKED|FAILED>|<short reason>
C|<id>|<path or symbol>|<change>
F|<id>|<path:line or symbol>|<verified fact>
D|<id>|<supporting record IDs>|<deduction>
A|<id>|<scope>|<assumption used>
U|<id>|<scope>|<unknown>
H|<id>|<category>|<location>|<decision required>|<blocked work>
V|<id>|<PASS|FAIL|NR>|<check or command>|<result>
W|<id>|<risk>|<evidence>
N|<ORCHESTRATOR|WORKER:<role>|<next action>
```

## Precision rules

- `F` requires direct evidence.
- `D` cites the `F` records that support it.
- `A` is permitted only when the contract allows it.
- `U` must not become a fact later.
- `H` gives the exact decision and affected work.
- `V|NR` means not run; never imply success.
- `DONE` means contracted worker work is complete, not that the whole task is production-ready.
- Do not repeat the contract, user request, or previously acknowledged records.

## Example

```text
S|PARTIAL|Mechanical structures created; duplicate semantics unresolved
C|C1|OutputActivationRequest.java|Created record with agreed fields
C|C2|OutputActivationMapper.java|Added field-for-field mapping
F|F1|OutputService#activate|Existing branch calls findByProcessId
H|H1|business|OutputService#activate|Choose reject or return existing|Service branch and two tests
V|V1|NR|module compile|Shell not available to this worker
N|ORCHESTRATOR|Decide H1, review diff, then delegate remaining tests
```
