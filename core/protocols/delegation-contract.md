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
