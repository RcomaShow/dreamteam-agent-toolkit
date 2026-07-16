---
name: measure
description: Compare direct work and DreamTeam routes using equal acceptance criteria, main-model and worker usage, duplicate reads, retries, and quality parity.
argument-hint: "<task class or completed run>"
disable-model-invocation: true
---

# DreamTeam Measure 0.2

Target: `$ARGUMENTS`

Record equivalent direct and DreamTeam runs:

```text
RUN|direct|task|result
RUN|dreamteam|task|profile|route|result
METRIC|main_turns|
METRIC|worker_turns|
METRIC|main_deep_reads|
METRIC|worker_deep_reads|
METRIC|duplicate_deep_reads|
METRIC|compression_ratio|
METRIC|main_reread_ratio|
METRIC|handoff_records|
METRIC|retries|
METRIC|quality_gates|
METRIC|usage_main|
METRIC|usage_workers|
METRIC|usage_total|
METRIC|elapsed_observed|
```

A saving is valid only with equivalent acceptance criteria and quality gates. Report separately total-token, main-model-token, and weighted-cost outcomes. Label estimates.
