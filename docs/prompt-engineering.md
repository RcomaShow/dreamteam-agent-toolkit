# Prompt Engineering Guidelines

## Worker prompts

- One role and one output contract.
- State what the worker may do and what it must never decide.
- Provide observable success criteria.
- Require source-linked evidence.
- Permit `unknown` and handoff.
- Bound files, turns, output, and retries.
- Use a fixed response template.
- Prevent spontaneous improvements.
- Ask for one correction hypothesis at a time.

## Orchestrator prompts

- Classify before delegating.
- Give decisions, not vague intentions.
- Close the file scope.
- Reserve risky decisions explicitly.
- Require exact verification.
- Inspect decision-critical evidence and every diff.
- Do not repeat delegated exploration.
- Do not treat worker confidence as proof.

## Prompt length

Put always-needed rules in the main prompt. Put detailed examples, schemas, and uncommon cases in references loaded on demand.
