# Roadmap

## 0.4.x — Stabilization

- Integrity-safe ledger idempotency and strict path provenance.
- Reproducible pricing/config context and ledger schema compatibility.
- Benchmark semantic validation, portability checks, and stability artifacts.

## 0.5.0 — Measurement-First Orchestration

- Separate cost, total-token, main-token, normalized-payload, and handoff metrics.
- Account explicitly for Lean root-executive overhead.
- Keep token gates shadow-only until paired calibration.
- Publish independent cost/token/payload/combined benchmark gates.
- Ship a Codex-native `AGENTS.md` adapter and explicit user skill.
- Preserve the 0.4 router as a compatibility and A/B baseline.

## 0.5.x — Evaluation and Context Engineering

- Representative Java, Python, TypeScript, infrastructure, migration, and test-generation suites.
- Cold/warm-cache cohorts, randomized order, confidence intervals, and bucket-specific calibration.
- Raw paired benchmark publication, coverage reporting, and property-based protocol tests.
- Deterministic repository capsules, blob/symbol/query cache, and progressive context disclosure.
- Provider-authoritative usage ingestion and reservation reconciliation.
- Provider token-count preflight where a stable provider API exposes it.
- Optional closed-context Batch executor.

## 0.6 — Durable Local Controller

- Idempotent task state machine, leases, cancellation, retry fingerprints, partial-failure recovery, and local DAG joins.
- Checkpoint restore and optional worktree isolation for independent writers.
- Calibrated token gates promoted from shadow mode only for proven task buckets.

## 0.7 — Adapter Conformance

- Codex execution/usage integration beyond the 0.5 instruction adapter.
- Gemini CLI adapter.
- Portable usage/event schema and DCP/2–CHP/2 conformance tests across providers.

## 1.0

- Published representative benchmark results, independent security review, signed artifacts, SBOM, parser fuzzing, provider-authoritative usage accounting where supported, and stable cross-adapter protocols.
