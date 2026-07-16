# Delegation Contract Protocol — DCP/1

A worker receives a closed contract. Omit unused records.

```text
G|<goal>
S+|<allowed scope>
S-|<excluded scope>
I|<input or verified reference>
K|<decision already made>
T|<requested action>
R|<decision reserved to orchestrator>
V|<allowed verification>
B|files=<n>;deep_reads=<n>;turns=<n>;records=<n>;retries=<n>
O|<required output>
```

## Rules

- One semantic item per record.
- `K` is authoritative; the worker applies it without reinterpretation.
- `R` marks a hard boundary. The worker may gather evidence but must not decide.
- `S+` is closed: files outside it require handoff.
- A missing decision is not permission to invent one.
- Budgets are upper bounds, not targets.
- Use stable references such as `path`, `Class#method`, or record IDs.

## Example

```text
G|Create the request model and mapper for output activation
S+|src/main/java/com/acme/output/dto;src/main/java/com/acme/output/mapper
S-|pom.xml;application.properties
I|ExistingActivationMapper.java
K|Fields are processId, activationType, requestedBy
T|Create request record and map it to OutputCommand
R|Validation rules;duplicate handling;public error contract
V|Compile the affected module
B|files=4;deep_reads=3;turns=6;records=18;retries=1
O|Modified files, evidence, verification state, and handoff points
```

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
