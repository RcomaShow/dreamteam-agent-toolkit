# DreamTeam 0.4.5 Worker Catalog

| Agent | Model | Effort | Role |
|---|---|---|---|
| `discovery-symbol-locator` | `haiku` | `low` | Locate exact files, symbols, definitions, and references for a bounded question. No flow analysis, design, or edits. |
| `discovery-flow-tracer` | `haiku` | `medium` | Trace a supplied entry point through calls, branches, state, integrations, side effects, and error paths. No broad symbol discovery or edits. |
| `discovery-pattern-miner` | `haiku` | `low` | Find and compare up to three analogous implementations, tests, or conventions for an already-defined structure or behavior. |
| `discovery-impact-mapper` | `haiku` | `medium` | Map callers, public contracts, tests, persistence, configuration, and integration surfaces affected by a proposed change. |
| `discovery-context-synthesizer` | `haiku` | `low` | Compress supplied files, excerpts, logs, or reports into source-linked facts, contradictions, unknowns, and decisions. No independent exploration. |
| `execution-scaffold-builder` | `haiku` | `low` | Create new mechanical structures from an approved blueprint: DTOs, records, enums, interfaces, resources, repositories, mappers, and service scaffolds. |
| `execution-mechanical-editor` | `haiku` | `low` | Apply a precise repetitive transformation to existing files after enumerating targets and exceptions. |
| `execution-bounded-logic` | `haiku` | `medium` | Implement completely specified local L1 logic with enumerated branches, explicit inputs/outputs, closed symbols, and targeted tests. |
| `execution-test-writer` | `haiku` | `medium` | Implement unit, component, or contract tests from an orchestrator-approved case matrix. Never decide the correct behavior. |
| `execution-documentation-updater` | `haiku` | `low` | Update bounded technical documentation from approved code changes, decisions, and verification results. No new product or architecture decisions. |
| `execution-sonnet-lead` | `sonnet` | `high` | Plan, implement, or integrate bounded L1/L2 work delegated by an Opus executive, especially when Haiku would require too much transferred reasoning context. |
| `verification-failure-triage` | `haiku` | `medium` | Diagnose verbose compilation, test, runtime, dependency, configuration, environment, or timeout failures without modifying files. |
| `verification-diff-auditor` | `haiku` | `medium` | Classify a bounded diff by mechanical, logical, contract, security, and scope risk so the orchestrator reviews only consequential regions. |
| `verification-test-gap-finder` | `haiku` | `low` | Compare specified branches and behavior against existing tests to identify missing cases without writing tests. |
| `coordination-decision-analyst` | `sonnet` | `high` | Resolve a bounded cross-domain L2 decision from compact evidence without rereading the repository or editing files. |
| `verification-independent-reviewer` | `sonnet` | `high` | Independently verify bounded M0/L1/L2 changes against an approved contract and test evidence. Never review its own authored change. |

Select the narrowest role. Do not run agents with overlapping question and scope. The executive owns every dispatch and transition.
