#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

mkdir -p "$(dirname -- 'CHANGELOG.md')"
cat > 'CHANGELOG.md' <<'__DT_V03_0000__'
# Changelog

All notable changes follow semantic versioning.

## [0.3.0] - 2026-07-16

### Added

- Dependency-free `dreamteam_runtime` control plane and CLI.
- Versioned Anthropic pricing catalogs for the Sonnet 5 introductory and standard pricing epochs.
- Canonical fresh/cache/output/Batch/tool usage accounting and USD repricing.
- Conservative 30-percent break-even gate with retry, escalation, quality, and history inputs.
- `sonnet-haiku` and `opus-sonnet-haiku` topologies.
- Three Sonnet lead agents for bounded L2 analysis, bounded L2 implementation, and independent verification under an Opus root.
- SQLite WAL source-read, event, permit, checkpoint, and route-sample ledger.
- Runtime `main_reread_ratio` enforcement through Claude Code plugin hooks.
- Verifiable `file:path:Lx-Ly@blob:...#sha256:...` CHP/2 fact anchors.
- Deterministic token-budgeted repository map with symbol/reference graph ranking and cache.
- Append-only head/summary/tail condensation plans with pinned and atomic event groups.
- Resumable DAG scheduler with independent parallel waves and successful-node reuse.
- Hard request, tool-call, token, and USD budgets with atomic parallel reservations.
- Closed-context Message Batch manifest builder and explicit retention acknowledgment.
- Paired benchmark schema, task archetypes, quality-parity analysis, confidence intervals, repricing, and bucket-scoped auto-demotion.
- `cost-proof` profile and class-specific independent verification policy.

### Changed

- Plugin and configuration schema version to 0.3.0 / version 2.
- Routing objective from advisory token heuristics to measured USD with shadow-to-enforce promotion.
- Agent generation to set explicit model and effort per role.
- `/dreamteam:run`, `measure`, `review`, and `doctor` for the two topology control plane.
- Routing fixtures to include `DOMAIN_LEAD`.

### Safety and compatibility

- Agents still cannot spawn agents; root remains the only dispatcher.
- C3 remains root-owned in every topology.
- The ledger persists no source content.
- Batch remains disabled by default.
- CHP/2 anchor validation is opt-in for legacy handoffs and required by the 0.3 cost-proof profile.

## [0.2.0] - 2026-07-16

- Added the DT-C1 constitution, five routes, M0/L1/L2/C3 criticality, the offload profile, DCP/2 and CHP/2, symbol-level ownership, thirteen specialized Haiku workers, `/dreamteam:doctor`, configuration schema, routing fixtures, and expanded structural/protocol tests.

## [0.1.0] - 2026-07-16

- Initial platform-independent core and Claude Code adapter.
__DT_V03_0000__
mkdir -p "$(dirname -- 'README.md')"
cat > 'README.md' <<'__DT_V03_0001__'
# DreamTeam 0.3

**Quality-owned multi-model engineering with a measured USD break-even gate.**

DreamTeam is a dependency-free orchestration toolkit for Claude Code and other agent runtimes. It keeps consequential decisions with a root model, routes bounded volume to cheaper models only when the full route is expected to save money, and verifies quality independently.

Version 0.3 turns the 0.2 charters into an executable control plane:

- versioned Anthropic pricing with fresh input, cache writes, cache reads, output, Batch, and tool cost;
- a conservative `hybrid <= 70% of direct` gate at quality parity;
- SQLite WAL accounting for source reads, checkpoints, permits, and route history;
- source anchors that bind path, line range, blob OID, and slice SHA-256;
- deterministic token-budgeted repo maps and head/summary/tail context plans;
- resumable DAG scheduling with independent parallel waves;
- hard request, tool-call, token, and USD budgets with parallel reservations;
- paired benchmark analysis and bucket-scoped auto-demotion;
- two model topologies.

## Topologies

### Sonnet → Haiku

Sonnet 5 is the final orchestrator. Haiku handles eligible discovery, M0 mechanical work, completely specified L1 work, and bounded verification evidence. C3 and unresolved L2 remain Sonnet-owned.

```text
/dreamteam:run profile=cost-proof topology=sonnet-haiku <task>
```

The benchmark baseline is a cached Sonnet-5-only run with the same acceptance criteria.

### Opus → Sonnet → Haiku

Opus 4.8 owns ambiguity, architecture, C3, and release. Sonnet domain leads handle root-bounded L2 analysis/implementation and independent verification. Haiku handles eligible volume, M0, and closed L1.

```text
/dreamteam:run topology=opus-sonnet-haiku <task>
```

Only the Opus root dispatches work. Sonnet and Haiku agents cannot create agents, so the hierarchy remains observable and auditable.

## Cost-proof rule

DreamTeam does not assume that delegation is cheaper. It prices the whole route:

```text
worker instructions + worker input/output/cache
+ handoff + root/lead verification
+ P(retry) × retry cost
+ P(escalation) × escalation cost
+ server-tool charges
```

Delegation is enforced only when its conservative upper cost is at least 30 percent below the conservative direct cost and the configured quality floor is preserved. New buckets start in shadow mode. Negative ROI demotes only the measured worker/task/size/cache bucket.

## Install and run

```text
/plugin marketplace add RcomaShow/dreamteam-agent-toolkit
/plugin install dreamteam@dreamteam-tools
/dreamteam:doctor
```

Repository-local tools:

```bash
python3 scripts/dreamteam.py doctor .
python3 scripts/dreamteam.py repo-map . --tokens 2048 --identifier OrderService
python3 scripts/dreamteam.py route route-input.json --date 2026-07-16
python3 scripts/dreamteam.py ledger summary .dreamteam/ledger.sqlite3 <run-id>
python3 scripts/dreamteam.py benchmark evals/results.jsonl --markdown
```

## Runtime safety

The Claude Code plugin registers hooks for source reads, Bash read bypasses, tool batches, subagent lifecycle, and stop. The ledger stores hashes, ranges, byte lengths, and event metadata—never source content. A root reread above the configured ratio requires an explicit decision, contradiction, C3, gate, or user permit.

Message Batch is a separate, opt-in lane for immutable closed-context tasks. It is not the same as a background Claude Code agent and requires explicit source-retention acknowledgment.

## Quality ownership

- **M0:** final diff invariant and targeted deterministic check.
- **L1:** specification-to-branch review, targeted tests, and anchor sampling.
- **L2:** verification at every decision point before dependent work.
- **C3:** root direct implementation/review and required checks.

Tests written by the authoring chain are useful evidence but cannot be the only independent final oracle.

## Benchmark status

The repository includes the paired USD methodology, schemas, task archetypes, repricing, confidence intervals, and auto-demotion logic. It intentionally publishes **no savings claim yet**: real Sonnet/Haiku and Opus/Sonnet/Haiku runs must be captured on representative tasks first.

## Validate

```bash
python3 scripts/sync_claude_adapter.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
```

The toolkit itself uses only the Python standard library. See `docs/v0.3-design.md`, `core/topologies/`, and `core/routing/` for the design.

## License

MIT
__DT_V03_0001__
mkdir -p "$(dirname -- 'ROADMAP.md')"
cat > 'ROADMAP.md' <<'__DT_V03_0002__'
# Roadmap

## 0.3 — Cost Proof and Cascades

- USD-aware routing and versioned pricing.
- Runtime read/checkpoint ledger and source anchors.
- Sonnet-Haiku and Opus-Sonnet-Haiku topologies.
- Independent verification, deterministic context reduction, hard budgets, and paired benchmark harness.

## 0.3.x — Measured Calibration

- Run the published task matrix under cold, warm-main, and steady-state cache modes.
- Publish raw usage, quality gates, paired confidence intervals, and pricing-epoch repricing.
- Calibrate route thresholds per worker/task/size/cache bucket.
- Promote only proven buckets from shadow to enforce.

## 0.4 — Adapter Conformance

- Codex and Gemini CLI runtime adapters.
- Cross-adapter event, anchor, pricing, and checkpoint conformance tests.
- Optional provider-neutral pricing catalogs.

## 1.0

- Stable runtime/protocol compatibility contract.
- Published benchmark corpus with reproducible acceptance oracles.
- External security review and signed release artifacts.
__DT_V03_0002__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/.claude-plugin/plugin.json')"
cat > 'adapters/claude-code/plugins/dreamteam/.claude-plugin/plugin.json' <<'__DT_V03_0003__'
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "dreamteam",
  "displayName": "DreamTeam",
  "version": "0.3.0",
  "description": "USD-aware, quality-gated Sonnet-Haiku and Opus-Sonnet-Haiku orchestration with runtime read accounting, resumable checkpoints, and paired benchmarks.",
  "author": {
    "name": "RcomaShow",
    "url": "https://github.com/RcomaShow"
  },
  "homepage": "https://github.com/RcomaShow/dreamteam-agent-toolkit",
  "repository": "https://github.com/RcomaShow/dreamteam-agent-toolkit",
  "license": "MIT",
  "keywords": [
    "agents",
    "orchestration",
    "cost-routing",
    "token-optimization",
    "quality-gates",
    "multi-model"
  ],
  "defaultEnabled": true
}
__DT_V03_0003__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/README.md')"
cat > 'adapters/claude-code/plugins/dreamteam/README.md' <<'__DT_V03_0004__'
# DreamTeam Claude Code Plugin 0.3

DreamTeam 0.3 adds a dependency-free orchestration control plane to the 0.2 charters.

Commands:

- `/dreamteam:run profile=cost-proof topology=sonnet-haiku <task>`
- `/dreamteam:run topology=opus-sonnet-haiku <task>`
- `/dreamteam:review`
- `/dreamteam:measure`
- `/dreamteam:doctor`

The plugin bundles:

- 13 specialized Haiku agents for bounded volume work;
- 3 Sonnet lead agents for L2 analysis/implementation and independent verification under an Opus root;
- versioned Anthropic USD catalogs;
- a SQLite WAL read/checkpoint/ROI ledger;
- Claude Code hooks that account source reads and enforce reread limits;
- deterministic repo maps, context compaction plans, DAG scheduling, budget reservations, batch manifests, and paired benchmark analysis.

The root session remains final owner. Agents cannot call agents. `sonnet-haiku` expects a Sonnet 5 root; `opus-sonnet-haiku` expects an Opus 4.8 root. Run `/dreamteam:doctor` before enforced routing or benchmarks.

No source content is persisted by the ledger. Message Batch is disabled by default and requires explicit source-retention acknowledgment.
__DT_V03_0004__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/bin/dreamteam_cli.py')"
cat > 'adapters/claude-code/plugins/dreamteam/bin/dreamteam_cli.py' <<'__DT_V03_0005__'
#!/usr/bin/env python3
from pathlib import Path
import os
import sys

PLUGIN = Path(__file__).resolve().parents[1]
LIB = PLUGIN / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))
os.environ.setdefault("DREAMTEAM_PRICING_DIR", str(PLUGIN / "data/pricing"))

from dreamteam_runtime.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
__DT_V03_0005__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/bin/dreamteam_hook.py')"
cat > 'adapters/claude-code/plugins/dreamteam/bin/dreamteam_hook.py' <<'__DT_V03_0006__'
#!/usr/bin/env python3
from pathlib import Path
import sys

LIB = Path(__file__).resolve().parents[1] / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from dreamteam_runtime.hook import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
__DT_V03_0006__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/hooks/hooks.json')"
cat > 'adapters/claude-code/plugins/dreamteam/hooks/hooks.json' <<'__DT_V03_0007__'
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read|Grep|Glob|Bash|Agent",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Read|Grep|Glob|Bash|Agent",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 15
          }
        ]
      }
    ],
    "PostToolBatch": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 15
          }
        ]
      }
    ],
    "SubagentStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 10
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_hook.py\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
__DT_V03_0007__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/skills/doctor/SKILL.md')"
cat > 'adapters/claude-code/plugins/dreamteam/skills/doctor/SKILL.md' <<'__DT_V03_0008__'
---
name: doctor
description: Validate DreamTeam 0.3 topology, full model mappings, effort, pricing epoch, hook runtime, read ledger, environment overrides, protocol anchors, and benchmark readiness.
argument-hint: "[optional project path]"
disable-model-invocation: true
---

# DreamTeam Doctor 0.3

Inspect without changing project configuration.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_cli.py" doctor ${ARGUMENTS:-.}
```

Then report:

```text
PLUGIN_VERSION|0.3.0
CONSTITUTION|DT-C1
PROTOCOL|DCP/2,CHP/2
TOPOLOGY|
PROFILE|
CONFIG_SOURCE|
ROOT_MODEL|
LEAD_MODEL|
WORKER_MODEL|
ROOT_EFFORT|
LEAD_EFFORT|
WORKER_EFFORT|
PRICING_CATALOG|
BILLING_SURFACE|
SUBAGENT_MODEL_OVERRIDE|
HOOKS_STATUS|
LEDGER_STATUS|
ANCHOR_VALIDATION|
BATCH_STATUS|
BENCHMARK_READY|
WARNINGS|
```

Benchmark readiness is false when model aliases are not resolved to the intended full IDs, an environment override changes subagent models, hooks cannot execute, strict tool accounting is disabled, source-content retention is inconsistent, the active pricing date has no unique catalog, or the actual root model does not match the topology. Do not expose secrets or full environment values.
__DT_V03_0008__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/skills/measure/SKILL.md')"
cat > 'adapters/claude-code/plugins/dreamteam/skills/measure/SKILL.md' <<'__DT_V03_0009__'
---
name: measure
description: Capture and analyze paired root-direct versus DreamTeam runs in USD with whole-tree model usage, cache accounting, retries, quality parity, and bucketed auto-demotion.
argument-hint: "<benchmark case or completed run>"
disable-model-invocation: true
---

# DreamTeam Measure 0.3

Target: `$ARGUMENTS`

1. Run `/dreamteam:doctor`. Reject the benchmark when full model IDs, effort, plugin version, hooks, pricing epoch, billing surface, tool permissions, or `CLAUDE_CODE_SUBAGENT_MODEL` differ from the declared setup.
2. Freeze commit, dirty state, prompt, acceptance hash, cache mode, and gates. Randomize arm order.
3. Arm A is root-direct only: Sonnet 5 only for `sonnet-haiku`, Opus only for the primary `opus-sonnet-haiku` baseline. Deny built-in and DreamTeam agents. A separate Sonnet-5-only comparison may be reported for the tri-tier topology but must not be mislabeled as the Opus baseline.
4. Arm B allows only models declared by the topology. Built-in or unrecorded agents invalidate the pair.
5. Capture whole-tree usage by full model ID: uncached input, 5m/1h cache writes, cache reads, output, server-tool cost, requests, tool calls, and batch status. Include retries, escalation, correction, and final verification needed to reach acceptance.
6. Record quality only from equivalent gates. Tests written by the implementation chain are not an independent oracle by themselves.
7. Store one JSON/JSONL record per arm using `evals/benchmark/schema.json`; label subscription data `api-equivalent`, not invoice USD.
8. Analyze with:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_cli.py" benchmark <runs.jsonl> \
  --catalog <catalog.json> --markdown --output <report.md>
```

9. Publish measured values only. Reprice the same raw usage under both pricing epochs when useful.
10. Promote delegation only when the exact bucket reaches the minimum sample count, quality floor, and conservative 30-percent saving. Demote a negative bucket to `MAIN_DIRECT`; do not disable the worker globally.
__DT_V03_0009__
