# Changelog

All notable changes follow semantic versioning.

## [0.4.0] - 2026-07-17

### Added

- Explicit `opus-sonnet` topology for Opus executive → Sonnet lead/reviewer execution.
- Concrete agent-role and execution-chain selection in route decisions.
- Runtime DCP/2 and CHP/2 parser with immutable ledger registration, contract, run, task, anchor, and reviewer binding.
- Durable SQLite charges distinct from active budget reservations.
- Stable project-root path resolver, protected configuration, staged blob-stable reads, and strict tool-event accounting.
- Benchmark pair invariants, cost recomputation, and per-bucket publication gates.
- Tracked-file-only deterministic release manifests.
- Sonnet implementation lead role and expanded adversarial test suite.

### Changed

- Profiles now change runtime thresholds, worker counts, retries, turns, and parallelism.
- Configured model aliases now affect candidate forecasts.
- Direct and C3 paths obey the hard run budget.
- Strict enforcement requires enabled SQLite telemetry and available hooks.
- Write delegation requires both a distinct verifier and non-zero verifier forecast.
- Plugin, docs, schemas, CI, and release tooling use 0.4 semantics.

### Security

- Outside-root paths, Git metadata, plugin data, symlinks, protected-config writes, composite shell reads, nested shell execution, and unidentifiable Agent dispatches fail closed in strict mode.
- Invalidations store hashes and categories rather than raw commands.
- Strict SubagentStop rejects unregistered or mismatched CHP/2 contracts, and bundled deterministic wrappers are allowlisted without opening generic shell execution.
- The plugin installs disabled by default and requires explicit enablement after configuration review.
- Release builds refuse dirty trees, untracked files, and symlinks.
- GitHub Actions dependencies are pinned to immutable commit SHAs with read-only repository permissions.

### Claim policy

- No universal savings claim is made.
- Billed USD and recomputed API-equivalent USD remain separate.
- Publication claims require complete quality parity and sample, margin, and positive lower-tail gates in every reported bucket.

## [0.3.0] - 2026-07-17

- Self-contained cost-proof runtime, hooks, anchors, ledger, benchmark, deterministic adapter generation, and artifact smoke tests.

## [0.2.0] - 2026-07-16

- Constitution, criticality, DCP/2/CHP/2, offload profile, and thirteen Haiku workers.

## [0.1.0] - 2026-07-16

- Initial platform-independent core and Claude Code adapter.
