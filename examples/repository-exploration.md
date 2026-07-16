# Repository Exploration

The orchestrator asks `repo-scout`:

```text
G|Find how export completion is persisted
S+|legacy-export-module
S-|generated;target
I|ExportScheduler#run
T|Trace direct flow, state changes, transaction boundary, retry, and tests
R|New microservice design;data ownership
V|Read-only
B|files=12;deep_reads=10;turns=8;records=30;retries=0
O|CHP/1 with max four critical references
```

The orchestrator verifies only the cited state transition, transaction boundary, and failure branch before designing the new flow.
