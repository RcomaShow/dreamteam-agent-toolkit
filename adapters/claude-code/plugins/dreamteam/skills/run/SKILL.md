---
name: run
description: Route an engineering task across the current orchestrator and bounded low-cost DreamTeam workers, optimizing total cost or main-model offload while preserving explicit ownership and quality gates.
argument-hint: "profile=<economy|balanced|offload|quality> <task>"
disable-model-invocation: true
---

# DreamTeam Run 0.2

Task: `$ARGUMENTS`

You are the orchestrator and final owner.

1. Read `${CLAUDE_SKILL_DIR}/references/constitution-kernel.md`.
2. Load `dreamteam.config.json` only when present; otherwise parse the profile, defaulting to `balanced`.
3. Classify the requested code/work as `M0`, `L1`, `L2`, or `C3`.
4. Apply hard gates, then choose exactly one route: `MAIN_DIRECT`, `WORKER_READ`, `WORKER_WRITE`, `HYBRID_EDIT`, or `HIGH_CAPABILITY_WORKER`.
5. Emit a compact route packet before delegation or editing.
6. Use the shortest sufficient worker chain. One worker at a time; workers never delegate.
7. Before each worker, issue DCP/2 with closed paths and symbol ownership. Reserve C3 and unresolved L2 decisions to the orchestrator.
8. Treat worker facts as claims. Verify decision-critical references, contradictions, consequential code, and required gates—never repeat the entire investigation.
9. Sonnet/main edits directly for C3 work, localized dense logic, or when delegation would require transferring most reasoning.
10. Haiku workers may edit M0 and fully specified L1 work. For L2, use hybrid ownership.
11. Resolve every handoff and unknown. Reuse/resume a compatible worker when supported instead of restarting.
12. Run final checks and report only gates actually achieved.

Load references only when needed:

- routes/criticality/offload: `${CLAUDE_SKILL_DIR}/references/routing-policy.md`
- worker selection: `${CLAUDE_SKILL_DIR}/references/worker-catalog.md`
- protocol syntax: `${CLAUDE_SKILL_DIR}/references/compact-protocol.md`
- budgets: `${CLAUDE_SKILL_DIR}/references/profiles.md`
- verification: `${CLAUDE_SKILL_DIR}/references/quality-gates.md`
- ready templates: `${CLAUDE_SKILL_DIR}/references/templates.md`
