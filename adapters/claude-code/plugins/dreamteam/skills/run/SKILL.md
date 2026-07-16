---
name: run
description: Run a token-aware engineering task with the current session as orchestrator and specialized DreamTeam workers for bounded exploration, compression, boilerplate, tests, failure triage, or mechanical edits.
argument-hint: "profile=<economy|balanced|quality> <task>"
disable-model-invocation: true
---

# DreamTeam Run

Task: `$ARGUMENTS`

You are the orchestrator and final owner.

1. Parse the profile; default to `balanced`.
2. Classify volume, repeatability, specification clarity, logical complexity, risk, and delegation overhead.
3. Work directly when the task is small, logically dense, high risk, or still ambiguous.
4. Delegate only a separable bounded unit:
   - `dreamteam:repo-scout` for broad read-only code evidence.
   - `dreamteam:context-synthesizer` for supplied verbose material.
   - `dreamteam:structure-builder` for specified boilerplate.
   - `dreamteam:test-writer` for an approved test matrix.
   - `dreamteam:failure-triage` for verbose failures.
   - `dreamteam:mechanical-editor` for closed repetitive edits.
5. Before delegation, issue a DCP/1 contract with goal, scope, decisions, reserved decisions, verification, budget, and required output.
6. Use one worker at a time for the same problem. Do not let workers delegate.
7. Treat worker facts as claims to verify. Inspect only decision-critical references and every written diff.
8. Resolve every `H` and material `U`. Redelegate only work made mechanical by your decision.
9. Run required final checks and report actual quality gates.

Load supporting references only when needed:

- Routing uncertainty: `${CLAUDE_SKILL_DIR}/references/routing-policy.md`
- Contract or handoff syntax: `${CLAUDE_SKILL_DIR}/references/compact-protocol.md`
- Profile budgets: `${CLAUDE_SKILL_DIR}/references/profiles.md`
- Final verification: `${CLAUDE_SKILL_DIR}/references/quality-gates.md`
- Ready-to-fill contracts: `${CLAUDE_SKILL_DIR}/references/templates.md`
