# Offload Policy

Optimization target: high-capability/main-model context and work.

Offload by default when a bounded worker can reliably perform:

- bulk repository search or symbol location;
- call-flow tracing and impact mapping;
- pattern comparison;
- context or log compression;
- scaffolding and repetitive edits;
- fully specified bounded logic;
- approved test implementation;
- failure triage, diff classification, and test-gap analysis.

The orchestrator retains:

- requirement interpretation and ambiguity resolution;
- architecture and business semantics;
- C3 code changes;
- public contracts and consequential error behavior;
- final ownership and quality gates.

## No duplicate work

The orchestrator verifies only decision-critical references, contradictions, consequential code, and required gates. It does not reproduce a worker investigation in full.

## Shortest sufficient chain

Use the minimum worker sequence. Return to the orchestrator whenever a decision is reached. Resume a compatible worker context instead of restarting when the runtime supports it.
