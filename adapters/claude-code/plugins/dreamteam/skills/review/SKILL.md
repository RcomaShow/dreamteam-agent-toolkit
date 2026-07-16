---
name: review
description: Review DreamTeam 0.2 routes, CHP/2 handoffs, symbol ownership, worker edits, and final quality gates without reproducing delegated investigations.
argument-hint: "[optional scope]"
disable-model-invocation: true
---

# DreamTeam Review 0.2

Scope: `$ARGUMENTS`

1. Read the route packet, DCP/2 contracts, CHP/2 handoffs, and task ledger.
2. Reject unsupported facts, deductions with missing evidence, hidden assumptions, invalid protocol records, unresolved handoffs, and false verification claims.
3. Confirm the route and M0/L1/L2/C3 classification remain correct.
4. Verify decision-critical references and every consequential or public-contract hunk.
5. For low-risk mechanical hunks, use diff classification, targeted sampling, compilation, and tests rather than rereading full files.
6. Confirm a single active owner per code region and no out-of-scope edits.
7. Resolve every `H` and material unknown. Redelegate only after the remaining work becomes bounded M0/L1.
8. Report `SCOPED`, `IMPLEMENTED`, `COMPILED`, `TESTED`, `REVIEWED`, and `VERIFIED` only when actually achieved.
