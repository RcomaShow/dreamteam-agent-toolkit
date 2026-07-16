# Migration Workflow

1. Existing legacy-analysis skill produces facts.
2. Orchestrator records decisions and unknowns in TLP/1.
3. `context-synthesizer` compresses overlapping analysis reports.
4. Orchestrator decides service boundaries, contracts, ownership, and reliability semantics.
5. `structure-builder` creates approved scaffolding.
6. Orchestrator implements critical flow logic.
7. `test-writer` implements the approved matrix.
8. `failure-triage` filters verbose failures if necessary.
9. Orchestrator reviews the complete diff and verifies acceptance gates.

DreamTeam complements domain-specific legacy skills; it does not replace them.
