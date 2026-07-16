# Repository Exploration

```text
ROUTE|WORKER_READ
CLASS|L2
WORKER_WORK|locate entry point, then trace bounded legacy flow
MAIN_WORK|interpret business semantics and migration consequences
```

Start with `discovery-symbol-locator`. If the entry point is found, issue a new closed DCP/2 contract to `discovery-flow-tracer`. The orchestrator verifies only the critical references returned in CHP/2.
