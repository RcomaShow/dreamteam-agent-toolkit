# Ready Templates

## Route

```text
ROUTE|WORKER_READ
CLASS|L2
MAIN_WORK|decisions and consequential edits
WORKER_WORK|bounded evidence collection
MAIN_VERIFY|decision-critical references
WORKER_VERIFY|source-linked CHP/2
EXPECTED_SAVING|avoid bulk main-context reads
RISK|state the primary routing risk
```

## Contract

```text
DCP|2
RUN|<run>
TASK|<task>
CONST|DT-C1
PROFILE|offload
G|<goal>
S+|<allowed scope>
S-|<excluded scope>
E+|<editable symbol>
E-|<reserved symbol>
I|<reference>
K|<decision>
T|<action>
R|<reserved decision>
V|<allowed check>
B|files=8;deep_reads=8;turns=8;records=20;retries=1
O|CHP/2 delta
```

## Bounded logic blueprint

```text
BLUEPRINT|B1
CLASS|L1
EDIT|Class#method
SIGNATURE|<signature>
BEHAVIOR|<enumerated deterministic rules>
RESERVED|public contract;transactions;security;idempotency
TESTS|<targeted cases and command>
```
