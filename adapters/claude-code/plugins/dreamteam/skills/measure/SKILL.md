---
name: measure
description: Design and record an A/B comparison between direct work and DreamTeam delegation using representative tasks, quality gates, context volume, retries, and available Claude Code usage data.
argument-hint: "<task class or completed task>"
disable-model-invocation: true
---

# DreamTeam Measure

Target: `$ARGUMENTS`

Create a fair comparison plan or summarize completed runs.

Record:

```text
RUN|direct|task|profile|result
RUN|dreamteam|task|profile|result
METRIC|main_turns|
METRIC|worker_turns|
METRIC|files_read_main|
METRIC|files_read_workers|
METRIC|handoff_records|
METRIC|retries|
METRIC|quality_gates|
METRIC|usage_main|
METRIC|usage_subagents|
METRIC|elapsed_observed|
```

Rules:

1. Use equivalent task scope and acceptance criteria.
2. Start clean sessions when comparing context consumption.
3. Use `/usage` and `/context` when available; label estimates.
4. A saving is valid only when required quality gates are equal.
5. Report whether total usage, high-capability-model usage, or both improved.
6. Identify delegation overhead and the break-even task shape.
