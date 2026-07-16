# Execution Routes

## MAIN_DIRECT

The orchestrator reads, decides, edits, and verifies. Use for localized but logically dense work, ambiguous semantics, high-risk changes, or when the delegation contract would be comparable to the implementation.

## WORKER_READ

A lower-cost read-only worker gathers evidence; the orchestrator decides and edits. Use for repository discovery, legacy tracing, impact analysis, pattern search, context compression, and failure diagnosis.

## WORKER_WRITE

A lower-cost worker edits fully specified M0 or L1 work; the orchestrator reviews proportionately to risk and runs final gates.

## HYBRID_EDIT

Workers handle discovery and mechanical/bounded implementation. The orchestrator owns L2/C3 regions and final review. This is the preferred path for mixed migration work.

## HIGH_CAPABILITY_WORKER

A separate high-capability worker isolates a difficult analysis or review. This route optimizes context isolation or quality, not model cost. It is disabled by default in `economy` and `offload`.
