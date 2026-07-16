# Token Optimization

## Optimize the right metric

Track:

- total tokens;
- high-capability-model tokens;
- repeated context;
- worker startup overhead;
- handoff output;
- retries;
- quality-equivalent completion.

A workflow can use more total tokens but fewer expensive-model tokens. Report both.

## Main levers

- route high-volume, low-ambiguity work;
- use read-only workers for verbose exploration;
- keep main-session model and effort stable;
- use closed contracts and record budgets;
- return delta handoffs;
- avoid overlapping workers;
- resume compatible scopes;
- filter long outputs before main-context ingestion;
- stop loops after bounded retries;
- keep skills and prompts narrow;
- lazy-load detailed references;
- compare against direct execution.

## Break-even intuition

Delegation is attractive when a worker can replace many file reads or a long log with a compact evidence report. It is unattractive when the orchestrator must reread nearly everything or the task is already localized.
