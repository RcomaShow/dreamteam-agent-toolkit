# Delegation Contract Protocol — DCP/2

DCP/2 is a compact, line-oriented closed contract. Use one semantic item per record and omit unused optional records.

```text
DCP|2
RUN|<run-id>
TASK|<task-id>
CONST|DT-C1
PROFILE|<economy|balanced|offload|quality>
G|<verifiable goal>
S+|<allowed path or scope>
S-|<excluded path or scope>
E+|<editable path#symbol>
E-|<reserved path#symbol>
I|<input or verified reference>
K|<authoritative decision>
T|<requested action>
R|<decision reserved to orchestrator>
V|<allowed verification>
B|files=<n>;deep_reads=<n>;turns=<n>;records=<n>;retries=<n>
O|CHP/2
```

## Executable rules

- `CONST` must be `DT-C1`; `PROFILE` must be a supported profile.
- Singleton records may occur exactly once.
- `B` must contain every supported non-negative budget key and its `records` limit must cover the contract itself.
- `K`, `R`, `E-`, `S+`, and `E+` are hard boundaries.
- Missing semantics are not permission to invent them.
- Compute the normalized `sha256:` contract hash and register the validated DCP immutably in the run ledger before dispatch.

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

# DCP/2 and CHP/2 Escaping

Protocols use `|` as a field separator. Within a field encode:

```text
\\  -> backslash
\|  -> literal pipe
\n  -> newline
\r  -> carriage return
```

Unknown escape sequences are invalid. Records are UTF-8 and one physical line each. Empty trailing fields are preserved. Parsers reject unsupported versions, duplicate singleton or item IDs, invalid references, invalid budgets, malformed status records, and mismatched contract bindings.
