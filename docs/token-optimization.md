# Token and Work Optimization 0.2

DreamTeam measures total tokens, main-model tokens, and weighted cost separately. The `offload` profile prioritizes main-model conservation.

The dominant failure mode is duplicated work: a worker reads broadly and the orchestrator rereads everything. DreamTeam therefore tracks compression ratio, main reread ratio, and duplicate deep reads. The orchestrator verifies only consequential evidence and code.

Specialized workers reduce instruction ambiguity, but every added worker also increases routing surface. Worker count is justified through evaluation, not aesthetics.
