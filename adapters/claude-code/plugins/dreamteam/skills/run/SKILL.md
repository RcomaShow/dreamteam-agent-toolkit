---
name: run
description: Route an engineering task through DreamTeam 0.3 Lean or Frontier topology using the bundled conservative runtime and explicit quality ownership.
argument-hint: "topology=<lean|frontier> profile=<economy|balanced|offload|quality> <task>"
disable-model-invocation: true
---

# DreamTeam Run 0.3

Task: `$ARGUMENTS`

You are the executive orchestrator and final owner.

1. Read `${CLAUDE_SKILL_DIR}/references/constitution-kernel.md` and load project `dreamteam.config.json`.
2. Classify the work as M0, L1, L2, or C3 and select a typed task kind.
3. Build the smallest deterministic repository capsule before broad model reads.
4. Produce explicit token forecasts for direct Sonnet, Haiku worker, Sonnet lead/verifier, and Frontier Opus executive.
5. Call the bundled router from `${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_route.py`; do not estimate the final gate only in prose.
6. Delegate only when the candidate clears config, calibration, reread, budget, escalation, verification, and USD gates.
7. Batch is a separate API lane and requires config opt-in, a real Batch executor, closed context, and retention confirmation.
8. Keep physical dispatch flat. Workers never spawn workers; the executive owns the DAG and every transition.
9. A writing worker may not be its own acceptance oracle. C3 and public-contract decisions remain executive-owned.
10. Checkpoint completed nodes, reuse compatible context, verify anchors, and compact only at phase boundaries.
11. Treat hook strict-mode invalidations as benchmark failures, not ignorable warnings.
12. Report actual gates, pricing catalog, selected and rejected costs, and measured results. Never claim savings without quality-parity evidence.

Load references only as needed:
- routing/topology: `${CLAUDE_SKILL_DIR}/references/routing-policy.md`
- workers: `${CLAUDE_SKILL_DIR}/references/worker-catalog.md`
- protocol: `${CLAUDE_SKILL_DIR}/references/compact-protocol.md`
- profiles: `${CLAUDE_SKILL_DIR}/references/profiles.md`
- quality: `${CLAUDE_SKILL_DIR}/references/quality-gates.md`
