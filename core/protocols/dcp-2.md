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
