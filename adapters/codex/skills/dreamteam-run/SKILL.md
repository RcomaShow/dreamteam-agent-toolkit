---
name: dreamteam-run
description: Run an engineering task with DreamTeam 0.5 measurement-first routing, bounded context, compact handoffs, and separate cost/token/quality metrics.
---

# DreamTeam Run for Codex

Use the project `AGENTS.md` DreamTeam kernel when present. The root session remains the final owner.

1. Classify the request as M0, L1, L2, or C3 before broad reads.
2. Build a minimal repository capsule from exact symbols, ranges, diffs, failures, and source-linked facts.
3. Establish a strong direct baseline. Do not compare DreamTeam against a deliberately inefficient full-tree read.
4. If child/subagent execution exists, delegate only a closed M0/L1 unit or bounded discovery task. Keep dispatch flat and reserve C3 decisions to the root.
5. Use compact DCP/2 instructions and CHP/2 deltas. Do not send narrative history when source anchors or exact decisions are enough.
6. Separate API-equivalent cost, total tokens, root/main-model tokens, normalized payload bytes, handoff overhead, rereads, retries, latency, and quality.
7. Token gates are shadow-only until paired calibration demonstrates quality parity. Never infer token savings merely from using a cheaper model.
8. For writes, require targeted checks and independent acceptance of consequential behavior. A writer is not its own acceptance oracle.
9. If delegation is unavailable or the whole-tree overhead does not clear the gate, stay `MAIN_DIRECT` while preserving capsule and measurement discipline.
10. End with a compact measurement report. Use `NR` for metrics the current Codex surface cannot expose rather than inventing values.
