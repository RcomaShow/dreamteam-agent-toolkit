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
