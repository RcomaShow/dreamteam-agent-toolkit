# Failure Triage

Give the worker the failing targeted command and a bounded module. It returns:

```text
S|DONE|First causal compilation error identified
F|F1|OutputMapperTest.java:71|Constructor now requires activationType
D|D1|F1|Test fixture is stale; confidence high
V|V1|FAIL|mvn -Dtest=OutputMapperTest test|Compilation failed before tests
N|WORKER:test-writer|Update the fixture within the approved test scope
```
