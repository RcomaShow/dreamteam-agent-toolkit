# Generic CLI Adapter

A runtime-neutral integration can implement:

```text
dreamteam run --profile balanced --task task.md
dreamteam worker repo-scout --contract contract.dcp
dreamteam validate handoff.chp
```

The orchestrator should persist a TLP/1 ledger and pass closed DCP/1 contracts to workers. Worker stdout should be valid CHP/1 records. This directory is a placeholder for a future reference implementation.
