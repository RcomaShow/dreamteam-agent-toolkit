# Contributing

DreamTeam separates stable concepts from platform adapters.

## Change categories

- `core/`: changes must remain platform- and model-independent.
- `workers/`: describe capabilities and boundaries without platform syntax.
- `adapters/<platform>/`: translate core concepts to one runtime.
- `docs/`: explain design decisions and tradeoffs.
- `examples/`: show grounded, bounded workflows.

## Pull request expectations

1. State the operational problem and expected savings.
2. Identify whether the change affects core semantics or only an adapter.
3. Add or update validation tests.
4. Keep prompts concise and evidence-oriented.
5. Do not add a worker if an existing worker can handle the task with a narrower contract.
6. Document security implications for new execution capabilities.

Run:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

For Claude Code adapter changes, also run when available:

```bash
claude plugin validate ./adapters/claude-code/plugins/dreamteam --strict
claude plugin validate .
```
