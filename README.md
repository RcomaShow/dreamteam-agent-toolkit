# DreamTeam Agent Toolkit

**The right agent for every task. Orchestrate smarter. Spend less.**

DreamTeam is a platform-independent toolkit for constitution-guided, token-aware multi-agent engineering. It routes bounded high-volume work to specialized low-cost workers while keeping consequential decisions, code, and final ownership with the orchestrator.

## 0.2 principles

- **Haiku handles volume; the orchestrator handles consequence.**
- Optimize total tokens, main-model tokens, and weighted cost separately.
- Use one of five explicit routes: `MAIN_DIRECT`, `WORKER_READ`, `WORKER_WRITE`, `HYBRID_EDIT`, or `HIGH_CAPABILITY_WORKER`.
- Classify work as `M0`, `L1`, `L2`, or `C3` before assigning edit ownership.
- Use DCP/2 contracts and CHP/2 handoffs with parsable validation.
- Avoid duplicated investigation and verify proportionately to risk.
- No Agent Teams, nested agents, hooks, or telemetry are enabled by default.

## Claude Code adapter

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
```

Commands:

```text
/dreamteam:run profile=offload <task>
/dreamteam:review
/dreamteam:measure
/dreamteam:doctor
```

Profiles:

- `economy`: minimize total usage;
- `balanced`: default weighted compromise;
- `offload`: minimize main/high-capability-model work;
- `quality`: expanded verification and optional isolated high-capability analysis.

## Worker families

- discovery: symbol location, flow tracing, pattern mining, impact mapping, context synthesis;
- execution: scaffolding, mechanical edits, bounded logic, tests, documentation;
- verification: failure triage, diff audit, test gaps.

## Validate

```bash
python scripts/sync_claude_adapter.py
python scripts/validate.py
python -m unittest discover -s tests -v
```

See `docs/v0.2-design.md`, `core/constitution/`, and `core/routing/` for the design.

## License

MIT
