# Delegation Contract Protocol — DCP/2

DCP/2 is a compact, line-oriented contract. Use one semantic item per record and omit unused optional records.

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
O|<required output>
```

## Rules

- `K` is authoritative and applied without reinterpretation.
- `R` and `E-` are hard boundaries.
- `S+` and `E+` are closed; expansion requires handoff.
- Missing semantics are not permission to invent them.
- Budgets are upper bounds, not targets.
- Stable references use `path`, `Class#method`, or record IDs.
- Escape `\\`, `\|`, and `\n` as defined in `escaping.md`.
- Compute a SHA-256 hash of the normalized contract when deterministic tooling is available.

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

# DCP/2 and CHP/2 Escaping

Protocols use `|` as a field separator.

Within a field encode:

```text
\\  -> backslash
\|  -> literal pipe
\n  -> newline
\r  -> carriage return
```

Unknown escape sequences are invalid. Records are UTF-8 and one physical line each. Empty trailing fields are preserved. Parsers must reject unsupported versions, duplicate evidence/change/handoff IDs, invalid references, and malformed status records.
