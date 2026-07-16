# DreamTeam Agent Toolkit

**The right agent for every task. Orchestrate smarter. Spend less.**

DreamTeam is a platform-independent toolkit for cost-aware, quality-gated multi-agent work. It separates reusable orchestration concepts from platform adapters, so the same routing, compact handoff, and worker design can be implemented in Claude Code, Codex, Gemini CLI, custom agent runtimes, or future systems.

## What DreamTeam optimizes

DreamTeam targets four operational costs:

| Cost | Mechanism |
|---|---|
| Model/context cost | Route verbose or mechanical work to lower-cost workers |
| Repeated work | Delta handoffs, task ledgers, and resumable scopes |
| Failed attempts | Stop-loss rules, bounded retries, and explicit escalation |
| Quality risk | Keep critical decisions with the orchestrator and require verification gates |

DreamTeam does **not** assume that delegation always saves tokens. The router delegates only when the expected context avoided in the orchestrator is greater than worker startup, handoff, and verification overhead.

## Architecture

```text
User request
    |
    v
Orchestrator / router
    |
    +-- direct execution for small or high-risk work
    |
    +-- read-only worker for exploration or compression
    |
    +-- write worker for mechanical, well-specified changes
    |
    +-- triage worker for verbose failures
    |
    v
Compact evidence-based handoff
    |
    v
Orchestrator decision, review, and final verification
```

The platform-independent definitions are under `core/` and `workers/`. Platform-specific packaging lives under `adapters/`.

## First working adapter: Claude Code

The Claude Code adapter ships a marketplace-compatible plugin named `dreamteam` with:

- `/dreamteam:run` — token-aware routing and orchestration
- `/dreamteam:review` — review worker output and resolve handoffs
- `/dreamteam:measure` — compare direct and delegated workflows
- six scoped workers: repository scout, context synthesizer, structure builder, test writer, failure triage, and mechanical editor

### Local test

```bash
claude --plugin-dir ./adapters/claude-code/plugins/dreamteam
```

Then run:

```text
/dreamteam:run profile=balanced <your task>
```

### Marketplace installation after publishing this repository

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
```

## Profiles

- **economy**: minimum worker turns, one retry, compact outputs
- **balanced**: default compromise between savings and confidence
- **quality**: broader verification and more orchestrator ownership

Profiles are policies, not guarantees. High-risk decisions remain with the orchestrator in every profile.

## Repository map

```text
core/                       Platform-independent protocols and policies
workers/                    Generic worker specifications and prompts
adapters/claude-code/       Working Claude Code marketplace/plugin adapter
adapters/codex/             Future adapter contract
adapters/gemini-cli/        Future adapter contract
adapters/generic-cli/       Runtime-agnostic integration example
docs/                       Architecture, token, prompting, and extension guides
examples/                   End-to-end task examples
scripts/                    Validation, synchronization, and release tooling
tests/                      Structural and protocol tests
```

## Validate and build

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build_release.py
```

If Claude Code is installed:

```bash
claude plugin validate ./adapters/claude-code/plugins/dreamteam --strict
claude plugin validate .
```

## Design principles

1. Delegate evidence gathering, not responsibility.
2. Prefer narrow workers over a universal worker.
3. Keep worker output smaller than the material it replaces.
4. Separate facts, deductions, unknowns, and decisions.
5. Use explicit scope and output budgets.
6. Stop after bounded failed attempts.
7. Keep critical logic, contracts, security, transactions, and final review with the orchestrator.
8. Measure savings on representative tasks instead of assuming them.

## Status

`0.1.0` is an initial architecture and Claude Code adapter. The core is intentionally stable and generic; adapters may evolve independently.

## License

MIT
