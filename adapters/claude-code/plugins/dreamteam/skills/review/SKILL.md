---
name: review
description: Review DreamTeam worker output, verify evidence and diffs, resolve handoffs, and apply final quality gates without repeating the whole delegated investigation.
argument-hint: "[optional scope]"
disable-model-invocation: true
---

# DreamTeam Review

Scope: `$ARGUMENTS`

1. Read the active CHP/1 handoff and task ledger.
2. Reject unsupported `F`, deductions without cited facts, hidden assumptions, and vague `H` records.
3. Open the decision-critical references and inspect every changed file.
4. Check scope, accidental edits, public contracts, business behavior, errors, security, transactions, idempotency, concurrency, and test adequacy as applicable.
5. Resolve each handoff. Delegate again only when the decision has made the remaining work mechanical.
6. Run the checks required for the stated quality gates.
7. Report gates as `SCOPED`, `IMPLEMENTED`, `COMPILED`, `TESTED`, `REVIEWED`, or `VERIFIED`; never infer a gate.
