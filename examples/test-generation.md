# Test Generation

```text
K|CASE1 valid request -> ACCEPTED and service called once
K|CASE2 missing processId -> behavior pending orchestrator decision
T|Implement CASE1 only
R|CASE2 expected behavior
```

The worker creates CASE1 and returns an `H` record for CASE2 instead of guessing validation semantics.
