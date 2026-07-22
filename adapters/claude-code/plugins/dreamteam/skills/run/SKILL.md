---
name: run
description: Route an engineering task through DreamTeam 0.4.4 Lean, Opus-Sonnet, or Frontier topology using strict runtime gates and explicit quality ownership.
argument-hint: "topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>"
disable-model-invocation: true
---

# DreamTeam Run 0.4.4

Task: `$ARGUMENTS`

You are the executive orchestrator and final owner.

1. Read `${CLAUDE_SKILL_DIR}/references/constitution-kernel.md` and load the project-root `dreamteam.config.json`. If it is missing, stop and direct the user to `/dreamteam:init`.
2. Classify the work as M0, L1, L2, or C3 and select a typed task kind.
3. Build the smallest deterministic repository capsule before broad model reads.
4. Produce explicit token forecasts for direct Sonnet, Haiku worker, Sonnet lead/reviewer, and Opus executive where the topology requires them.
5. Call `${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_route.py`; never decide the final gate only in prose.
6. Stop immediately on `BLOCKED`. Delegate only when calibration, reread, budget, escalation, strict-hook, verification, and USD gates pass.
7. `opus-sonnet` is an explicit Opus executive → `execution-sonnet-lead` bounded implementation path. Authored changes must go to `verification-independent-reviewer`, a different Sonnet agent identity. The topology contains no hidden Haiku usage.
8. `frontier` is Opus → Sonnet → Haiku and must account for every active stage.
9. Batch requires config opt-in, a real Batch executor, closed context, and retention confirmation.
10. Keep physical dispatch flat. Workers never spawn workers; the executive owns the DAG and every transition.
11. Before Agent dispatch set `DREAMTEAM_NEXT_AGENT_USD_MICROS` to the selected node reservation and preserve the hook `tool_use_id`. Bundled DreamTeam scripts are trusted deterministic wrappers. Any other Bash check requires the operator to pre-authorize the SHA-256 of the exact command in `DREAMTEAM_ALLOWED_BASH_SHA256`; an inline export is not permission.
12. A writing worker may not be its own acceptance oracle. C3 and public-contract decisions remain executive-owned.
13. Normalize, validate, and register each DCP/2 before dispatch with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_protocol.py" <contract.dcp2> --hash --bind`. The SubagentStop hook rejects CHP/2 whose run, task, or contract hash is not registered, and also validates current anchors and reviewer separation.
14. Treat hook invalidations, changed config hashes, unaccountable reads, stale anchors, and budget failures as run failures.
15. Report the pricing catalog, selected and rejected cost, concrete agent role, execution chain, actual gates, and measured results. Never claim savings without paired quality evidence.

Load references only as needed:
- routing/topology: `${CLAUDE_SKILL_DIR}/references/routing-policy.md`
- workers: `${CLAUDE_SKILL_DIR}/references/worker-catalog.md`
- protocol: `${CLAUDE_SKILL_DIR}/references/compact-protocol.md`
- profiles: `${CLAUDE_SKILL_DIR}/references/profiles.md`
- quality: `${CLAUDE_SKILL_DIR}/references/quality-gates.md`
