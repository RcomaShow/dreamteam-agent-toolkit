# Ready-to-fill templates

## Exploration

```text
G|Answer the bounded repository question
S+|<modules/directories>
S-|<excluded areas>
I|<entry point>
T|Find definitions, callers, branches, side effects, tests, and at most three analogues
R|Architecture;business semantics;implementation
V|Read-only evidence review
B|files=12;deep_reads=10;turns=8;records=30;retries=0
O|CHP/1;max four critical files
```

## Structure

```text
G|Create the specified structures
S+|<closed file list or directory>
S-|<build/global configuration>
I|<reference implementation>
K|<signatures and fixed decisions>
T|<mechanical structures>
R|Business logic;errors;transactions;security
V|<authorized targeted check or NR>
B|files=8;deep_reads=3;turns=8;records=25;retries=1
O|CHP/1 changes and exact handoffs
```

## Tests

```text
G|Implement the approved test matrix
S+|<test files>
S-|Production files
K|<case matrix>
T|Write tests and run <target command>
R|Correct behavior not already specified
V|<target command>
B|files=4;deep_reads=3;turns=10;records=30;retries=2
O|CHP/1 cases, result, and ambiguities
```
