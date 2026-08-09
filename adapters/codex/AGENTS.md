# DreamTeam 0.5 — Codex Project Adapter

Mission: minimize repeated context, total token load, main-model token load, and cost without lowering verified quality.

## Operating kernel

- The root Codex session owns the final result and all consequential decisions.
- Classify work before broad reads: `M0` mechanical, `L1` bounded logic, `L2` mixed/ambiguous, `C3` consequential.
- Build the smallest repository capsule that can answer the current question. Prefer exact symbols, ranges, diffs, test failures, and source-linked facts over whole-file or whole-tree reads.
- Do not repeat a delegated investigation in the root session unless evidence conflicts or a reserved decision requires it.
- Never treat a cheaper model or child agent as evidence of token savings. Cost, total tokens, main-model tokens, normalized payload bytes, rereads, retries, and quality are separate metrics.
- No savings claim is empirical until a paired direct baseline passes the same quality oracle.

## Routing

Use `MAIN_DIRECT` when the context is already hot, the task is small, requirements are ambiguous, a C3 decision is involved, calibration is missing, or delegation would not clear its whole-tree overhead.

When the Codex runtime exposes child/subagent execution, delegate only a bounded M0/L1 unit or evidence-gathering task with explicit scope, inputs, exclusions, verification, and budget. Keep dispatch flat: a child may not create another child.

If child/subagent execution is unavailable, remain `MAIN_DIRECT` and still apply the same capsule, reread, and measurement discipline. DreamTeam must improve a strong direct baseline, not a deliberately inefficient one.

## DCP/2 delegation contract

Before a child is invoked, define only the records that add decision value:

```text
DCP|2
RUN|<run-id>
TASK|<task-id>
CONST|DT-C1
PROFILE|<economy|balanced|offload|quality>
G|<verifiable goal>
S+|<allowed scope>
S-|<excluded scope>
E+|<editable symbol if any>
E-|<reserved symbol if any>
I|<verified input or source anchor>
K|<authoritative decision>
T|<requested action>
R|<decision reserved to root>
V|<targeted verification>
B|files=<n>;deep_reads=<n>;turns=<n>;records=<n>;retries=<n>
O|CHP/2
```

Do not invent semantics missing from the contract.

## CHP/2 return

A delegated child returns a decision-relevant delta rather than a narrative recap:

```text
CHP|2
RUN|<run-id>
TASK|<task-id>
CONTRACT|<hash-or-local-binding>
S|<DONE|PARTIAL|BLOCKED|FAILED>|<reason>
E|<id>|FACT|<source>|<claim>
E|<id>|DEDUCTION|<supporting ids>|<claim>
C|<id>|<path#symbol>|<change>
H|<id>|<category>|<location>|<decision required>|<blocked work>
V|<id>|<PASS|FAIL|NR>|<check>|<result>
N|<ROOT|CHILD:role>|<next action>
```

A writing child cannot be its own acceptance oracle. Review consequential changes independently.

## Measurement-first report

For a DreamTeam run, report when available:

- selected route and criticality;
- direct vs candidate API-equivalent cost;
- direct vs candidate total tokens;
- direct vs candidate root/main-model tokens;
- normalized source/payload bytes;
- handoff overhead, reread bytes, retries, escalations, and failed attempts;
- quality oracle result and checks actually executed.

Keep token gates in shadow mode until a representative paired benchmark calibrates them. If a metric cannot be measured by the current Codex surface, mark it `NR`; do not estimate it silently.
