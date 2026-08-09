---
name: run
description: Route an engineering task through DreamTeam 0.5 with whole-tree cost accounting, token telemetry, strict runtime gates, and explicit quality ownership.
argument-hint: "topology=<lean|opus-sonnet|frontier> profile=<economy|balanced|offload|quality> <task>"
disable-model-invocation: true
---

# DreamTeam Run 0.5

Task: `$ARGUMENTS`

You are the executive orchestrator and final owner.

1. Read `${CLAUDE_SKILL_DIR}/references/constitution-kernel.md` and load the project-root `dreamteam.config.json`. If it is missing, stop and direct the user to `/dreamteam:init`.
2. Classify the work as M0, L1, L2, or C3 and select a typed task kind.
3. Build the smallest deterministic repository capsule before broad model reads. Record normalized source bytes as well as provider token forecasts where available.
4. Forecast the direct baseline and every active DreamTeam component. **Lean now requires an explicit Sonnet executive usage forecast before delegation**; the root executive is not free. Opus-Sonnet and Frontier continue to require every active tier.
5. Call `${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_route.py`; never decide the final gate only in prose. The 0.5 router reports API-equivalent USD, total tokens, main-model tokens, and shadow token gates separately.
6. Token gates are shadow-only by default until paired calibration exists. Do not turn a cheaper-model cost saving into a token-saving claim. `--enforce-token-gates` is an explicit policy choice, not a default claim.
7. Stop immediately on `BLOCKED`. Delegate only when calibration, reread, budget, escalation, strict-hook, verification, and USD gates pass. A failed token gate must be surfaced even in shadow mode.
8. `opus-sonnet` is an explicit Opus executive → `execution-sonnet-lead` bounded implementation path. Authored changes must go to `verification-independent-reviewer`, a different Sonnet agent identity. The topology contains no hidden Haiku usage.
9. `frontier` is Opus → Sonnet → Haiku and must account for every active stage.
10. Batch requires config opt-in, a real Batch executor, closed context, and retention confirmation.
11. Keep physical dispatch flat. Workers never spawn workers; the executive owns the DAG and every transition.
12. Before Agent dispatch set `DREAMTEAM_NEXT_AGENT_USD_MICROS` to the selected node reservation and preserve the hook `tool_use_id`. Bundled DreamTeam scripts are trusted deterministic wrappers. Any other Bash check requires the operator to pre-authorize the SHA-256 of the exact command in `DREAMTEAM_ALLOWED_BASH_SHA256`; an inline export is not permission.
13. A writing worker may not be its own acceptance oracle. C3 and public-contract decisions remain executive-owned.
14. Normalize, validate, and register each DCP/2 before dispatch with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dreamteam_protocol.py" <contract.dcp2> --hash --bind`. The SubagentStop hook rejects CHP/2 whose run, task, or contract hash is not registered, and also validates current anchors and reviewer separation.
15. Treat hook invalidations, changed config hashes, unaccountable reads, stale anchors, and budget failures as run failures.
16. Report the pricing catalog, selected and rejected cost, concrete agent role, execution chain, expected total-token savings, expected main-token savings, actual gates, and measured results. `empirical_claim_allowed=false` remains mandatory until a paired benchmark oracle establishes quality parity.

Load references only as needed:
- routing/topology: `${CLAUDE_SKILL_DIR}/references/routing-policy.md`
- workers: `${CLAUDE_SKILL_DIR}/references/worker-catalog.md`
- protocol: `${CLAUDE_SKILL_DIR}/references/compact-protocol.md`
- profiles: `${CLAUDE_SKILL_DIR}/references/profiles.md`
- quality: `${CLAUDE_SKILL_DIR}/references/quality-gates.md`
