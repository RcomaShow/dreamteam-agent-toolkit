#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

mkdir -p "$(dirname -- 'core/routing/escalation-policy.md')"
cat > 'core/routing/escalation-policy.md' <<'__DT_V03_0020__'
# Escalation Policy 0.3

Escalation returns ownership or capability; it never silently swaps models.

Escalate when:

- a reserved or consequential decision is required;
- evidence conflicts or an anchor is stale;
- scope or symbol ownership must expand;
- a public contract, security, transaction, concurrency, idempotency, distributed consistency, migration, destructive action, retry/compensation, or backward-compatibility choice is involved;
- two bounded attempts fail on the same cause;
- required information is unavailable;
- verification contradicts the assumed behavior;
- the actual route can no longer meet its USD/quality bound.

## Continuation versus escalation

- Same model tier, goal, scope, and owner: resume the existing checkpoint/history.
- Different model tier or owner: create a new node using validated source anchors, authoritative decisions, and completed checkpoints.
- Preserve successful sibling nodes; retry only the failed node.

An escalation record includes location, source anchors, decision required, blocked work, current measured/estimated cost, completed checkpoints, and recommended next owner.
__DT_V03_0020__
mkdir -p "$(dirname -- 'core/routing/execution-routes.md')"
cat > 'core/routing/execution-routes.md' <<'__DT_V03_0021__'
# Execution Routes 0.3

## MAIN_DIRECT

The root reads, decides, edits, and verifies. Use for localized decision-dense work, C3, ambiguous semantics, warm context that is cheaper to reuse, or any route that fails the USD/quality gate.

## WORKER_READ

A Haiku read-only worker gathers and compresses evidence. The root or Sonnet lead decides and edits. Use for repository discovery, flow tracing, impact analysis, pattern search, context/log compression, failure diagnosis, diff classification, and test-gap analysis.

## WORKER_WRITE

A Haiku worker edits fully specified M0 or L1 work. A different owner performs the required final gate.

## HYBRID_EDIT

In the Sonnet-Haiku topology, Haiku handles discovery and mechanical/bounded pieces while the Sonnet root owns L2/C3 and final review.

## DOMAIN_LEAD

In the Opus-Sonnet-Haiku topology, a Sonnet lead handles a root-bounded L2 analysis or implementation region. Opus supplies authoritative decisions and retains all unresolved L2, C3, public-contract, and final-release ownership. Lead agents never delegate.

## HIGH_CAPABILITY_WORKER

A separate high-capability agent isolates difficult analysis or review. This route optimizes context isolation or quality, not cost, and requires explicit justification. It is distinct from the normal Sonnet domain lead under an Opus topology.
__DT_V03_0021__
mkdir -p "$(dirname -- 'core/routing/offload-policy.md')"
cat > 'core/routing/offload-policy.md' <<'__DT_V03_0022__'
# Offload Policy 0.3

Offload bounded volume only when the full route is expected to save USD at quality parity.

Eligible work includes bulk search, symbol location, flow/impact mapping, pattern comparison, context/log compression, scaffolding, repetitive edits, closed bounded logic, approved tests, documentation, failure triage, diff classification, and test-gap analysis.

The root retains requirement interpretation, architecture, unresolved business semantics, C3, public contracts, consequential errors, ownership transitions, and final success. In the tri-tier topology, Sonnet leads may receive root-closed L2 regions but do not inherit root authority.

## No duplicate work

The root verifies decision-critical anchors, contradictions, consequential code, and required gates. It does not replay the worker investigation. The runtime ledger measures duplicate and overlapping source reads.

## Shortest resumable graph

Use the fewest nodes that remove expensive root work. Return to root at every decision boundary. Resume the same model/goal checkpoint; cross-model escalation starts a new agent from validated anchors. Successful sibling nodes are never rerun merely because another parallel node failed.
__DT_V03_0022__
mkdir -p "$(dirname -- 'core/routing/read-ledger.md')"
cat > 'core/routing/read-ledger.md' <<'__DT_V03_0023__'
# Runtime Read Ledger 0.3

The read ledger turns the 0.2 reread target into an observable runtime invariant.

## Storage

SQLite WAL stores append-only run events, source-read spans, permits, checkpoints, and route samples. It stores no source text. A deep read records:

```text
run_id, owner, agent_id, tool
repository-relative path
git-compatible blob OID
start/end line
SHA-256 of the exact slice
per-line byte lengths
read class and depth
timestamp
```

The main reread ratio is computed over unique source bytes for the same path and blob:

```text
bytes read by worker/lead and later read by main
------------------------------------------------
unique bytes read by worker/lead
```

This unit is tokenizer-independent. Model token usage is accounted separately for USD.

## Enforcement

Claude Code plugin hooks observe `Read`, `Grep`, `Glob`, `Bash`, `Agent`, subagent lifecycle, tool batches, and stop. Before a main `Read`, the hook computes the projected ratio. Above the limit it:

- emits a warning in shadow mode;
- asks or denies in enforce mode;
- allows a one-use permit for `DECISION`, `CONTRADICTION`, `C3`, `GATE`, or explicit user review.

Strict benchmark mode blocks raw source reads through Bash because their spans cannot be measured reliably. `Read`, `Grep`, and `Glob` remain available.

## Anchors

Repository facts use:

```text
file:<path>:L<start>-L<end>@blob:<oid>#sha256:<slice>
```

`protocol_v2.py --require-anchors --verify-anchors` checks the grammar, current blob, and slice hash. A changed file invalidates stale anchors rather than silently reusing them.
__DT_V03_0023__
mkdir -p "$(dirname -- 'core/routing/routing-policy.md')"
cat > 'core/routing/routing-policy.md' <<'__DT_V03_0024__'
# Routing Policy 0.3

1. Select `sonnet-haiku` or `opus-sonnet-haiku` and verify the root model.
2. Classify every region as M0, L1, L2, or C3.
3. Apply consequence, contract, acceptance, ownership, read-accounting, and independent-gate hard rules.
4. Build direct and delegated whole-route usage plans in USD.
5. Choose exactly one route: `MAIN_DIRECT`, `WORKER_READ`, `WORKER_WRITE`, `HYBRID_EDIT`, `DOMAIN_LEAD`, or `HIGH_CAPABILITY_WORKER`.
6. In shadow mode record the recommendation and execute direct. In enforce mode delegate only when the conservative saving and quality gate pass.
7. Schedule the shortest root-controlled DAG. Only independent nodes may share a parallel wave.
8. Checkpoint every node and resume completed work instead of restarting it.

## Direct hard gates

Use root direct ownership when:

- C3, architecture, unresolved business semantics, public contracts, security, transactions, concurrency, idempotency, distributed consistency, migrations, destructive behavior, retry/compensation, or backward compatibility is involved;
- acceptance criteria or symbol ownership are not closed;
- delegation transfers most of the reasoning or the root must inspect almost all source anyway;
- projected root reread exceeds the configured ratio without a justified permit;
- strict accounting cannot observe a source read;
- final verification would come only from the authoring chain;
- the USD/quality gate fails or the route bucket is demoted.

## Topology ownership

- Sonnet-Haiku: Sonnet root owns unresolved L2, C3, and final success.
- Opus-Sonnet-Haiku: Opus root owns ambiguity, architecture, C3, and release; Sonnet leads receive closed L2 regions; Haiku receives volume, M0, and fully specified L1.

File count never overrides criticality or the measured cost gate.
__DT_V03_0024__
mkdir -p "$(dirname -- 'core/routing/token-aware-routing.md')"
cat > 'core/routing/token-aware-routing.md' <<'__DT_V03_0025__'
# Token and Context Signals 0.3

DreamTeam still records total tokens, root-model tokens, compression ratio, main reread ratio, duplicate reads, turns, and handoff size. These are diagnostic signals, not economic proof.

The primary cost-proof objective is:

```text
measured_usd_at_quality_parity
```

A model family may tokenize identical text differently, and cache reads may be much cheaper than fresh worker input. Therefore token counts are never converted into a route decision without model-specific pricing and cache state.

Initial discovery priors may use compression and reread estimates, but every new bucket starts in shadow mode. The old targets `compression_ratio >= 4.0` and `main_reread_ratio <= 0.35` remain historical evaluation references, not guarantees. The 0.3 cost-proof defaults are more conservative (`8.0` and `0.20`) and still require the USD gate.
__DT_V03_0025__
mkdir -p "$(dirname -- 'core/schemas/dreamteam-config.schema.json')"
cat > 'core/schemas/dreamteam-config.schema.json' <<'__DT_V03_0026__'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/RcomaShow/dreamteam-agent-toolkit/core/schemas/dreamteam-config.schema.json",
  "title": "DreamTeam Configuration 0.3",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "version": {"const": 2},
    "constitution": {"type": "string", "const": "DT-C1", "default": "DT-C1"},
    "profile": {
      "enum": ["economy", "balanced", "offload", "quality", "cost-proof"],
      "default": "cost-proof"
    },
    "topology": {
      "enum": ["sonnet-haiku", "opus-sonnet-haiku"],
      "default": "sonnet-haiku"
    },
    "models": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "root": {"type": "string", "minLength": 1},
        "lead": {"type": ["string", "null"]},
        "worker": {"type": "string", "minLength": 1},
        "effort": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "root": {"enum": ["low", "medium", "high", "max"]},
            "lead": {"enum": ["low", "medium", "high", "max"]},
            "worker": {"enum": ["low", "medium", "high", "max"]}
          }
        }
      },
      "required": ["root", "worker"]
    },
    "pricing": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "provider": {"const": "anthropic"},
        "catalogDir": {"type": "string", "default": "core/pricing"},
        "catalog": {"type": ["string", "null"]},
        "currency": {"const": "USD"},
        "billingSurface": {
          "enum": ["api", "subscription"],
          "default": "api"
        }
      },
      "required": ["provider", "currency", "billingSurface"]
    },
    "routing": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "objective": {"const": "usd", "default": "usd"},
        "decisionMode": {"enum": ["shadow", "enforce"], "default": "shadow"},
        "minimumSavingsMargin": {"type": "number", "minimum": 0, "exclusiveMaximum": 1, "default": 0.3},
        "qualityTolerance": {"type": "number", "minimum": 0, "maximum": 1, "default": 0},
        "minimumQuality": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.95},
        "confidenceBuffer": {"type": "number", "minimum": 0, "exclusiveMaximum": 1, "default": 0.1},
        "minimumHistorySamples": {"type": "integer", "minimum": 1, "default": 5},
        "minimumHistoryQualityPassRate": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.95},
        "targetCompressionRatio": {"type": "number", "minimum": 1, "default": 8},
        "maxMainRereadRatio": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.2},
        "directMaxLocalFiles": {"type": "integer", "minimum": 1, "default": 2},
        "maxActiveWorkers": {"type": "integer", "minimum": 1, "maximum": 8, "default": 2},
        "allowParallelIndependent": {"type": "boolean", "default": true},
        "autoDemoteNegativeRoi": {"type": "boolean", "default": true},
        "bucketDimensions": {
          "type": "array",
          "items": {"enum": ["worker", "taskKind", "criticality", "size", "route", "model", "effort", "cacheMode", "adapterVersion"]},
          "uniqueItems": true,
          "default": ["worker", "taskKind", "criticality", "size", "cacheMode"]
        }
      },
      "required": ["objective", "decisionMode", "minimumSavingsMargin", "maxMainRereadRatio"]
    },
    "runtime": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ledgerPath": {"type": "string", "default": ".dreamteam/ledger.sqlite3"},
        "enforceReadLedger": {"type": "boolean", "default": true},
        "rereadEnforcementAction": {"enum": ["ask", "deny"], "default": "ask"},
        "requireFactAnchors": {"type": "boolean", "default": true},
        "verifyAnchors": {"type": "boolean", "default": true},
        "checkpointEveryNode": {"type": "boolean", "default": true},
        "resumeCompletedNodes": {"type": "boolean", "default": true},
        "storeSourceContent": {"const": false}
      },
      "required": ["enforceReadLedger", "storeSourceContent"]
    },
    "context": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "strategy": {"const": "head-summary-tail", "default": "head-summary-tail"},
        "repoMapTokens": {"type": "integer", "minimum": 0, "default": 2048},
        "maxTokens": {"type": "integer", "minimum": 1024, "default": 80000},
        "softTriggerRatio": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1, "default": 0.75},
        "targetRatio": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1, "default": 0.45},
        "keepFirst": {"type": "integer", "minimum": 0, "default": 2},
        "keepLast": {"type": "integer", "minimum": 1, "default": 12},
        "pollingEvents": {"type": "integer", "minimum": 1, "default": 4},
        "minimumProgress": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1, "default": 0.1},
        "clipToolOutputCharacters": {"type": "integer", "minimum": 1000, "default": 100000},
        "pinTags": {"type": "array", "items": {"type": "string"}, "default": ["decision", "contract", "anchor", "gate"]}
      }
    },
    "verification": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "independentGateRequired": {"type": "boolean", "default": true},
        "M0": {"const": "gate-final"},
        "L1": {"const": "spec-branch-review-and-targeted-tests"},
        "L2": {"const": "verify-at-decision-points"},
        "C3": {"const": "root-direct-review"},
        "requireTargetedTest": {"type": "boolean", "default": true},
        "allowFullSuite": {"enum": ["root-only", "allowed"], "default": "root-only"}
      },
      "required": ["independentGateRequired", "M0", "L1", "L2", "C3"]
    },
    "batch": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "enabled": {"type": "boolean", "default": false},
        "closedContextOnly": {"const": true},
        "sourceRetentionAcknowledged": {"type": "boolean", "default": false},
        "allowedRoles": {
          "type": "array",
          "items": {"enum": ["context-synthesizer", "diff-auditor", "test-gap-finder", "classifier"]},
          "uniqueItems": true,
          "default": ["context-synthesizer", "diff-auditor", "test-gap-finder"]
        }
      },
      "required": ["enabled", "closedContextOnly", "sourceRetentionAcknowledged"]
    },
    "benchmark": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "strictToolAccounting": {"type": "boolean", "default": true},
        "paired": {"const": true},
        "baseline": {"enum": ["root-direct", "sonnet-5-direct"], "default": "root-direct"},
        "randomizeArmOrder": {"type": "boolean", "default": true},
        "cacheModes": {
          "type": "array",
          "items": {"enum": ["cold", "warm-main", "steady-state"]},
          "uniqueItems": true,
          "default": ["cold", "warm-main"]
        },
        "publishMeasuredOnly": {"const": true}
      },
      "required": ["strictToolAccounting", "paired", "publishMeasuredOnly"]
    },
    "budgets": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "maxRunUsd": {"type": ["number", "null"], "minimum": 0},
        "maxRequests": {"type": "integer", "minimum": 1, "default": 50},
        "maxToolCalls": {"type": "integer", "minimum": 1, "default": 200},
        "maxInputTokens": {"type": ["integer", "null"], "minimum": 1},
        "maxOutputTokens": {"type": ["integer", "null"], "minimum": 1},
        "maxWorkerTurns": {"type": "integer", "minimum": 1, "default": 10},
        "maxWorkerChain": {"type": "integer", "minimum": 1, "maximum": 4, "default": 3},
        "maxRetries": {"type": "integer", "minimum": 0, "default": 1}
      }
    },
    "telemetry": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "enabled": {"type": "boolean", "default": false},
        "storeSourceContent": {"const": false}
      },
      "required": ["storeSourceContent"]
    }
  },
  "required": ["version", "topology", "models", "pricing", "routing", "runtime", "verification"],
  "allOf": [
    {
      "if": {"properties": {"topology": {"const": "opus-sonnet-haiku"}}},
      "then": {
        "properties": {
          "models": {
            "required": ["root", "lead", "worker"],
            "properties": {"lead": {"type": "string", "minLength": 1}}
          }
        }
      }
    }
  ]
}
__DT_V03_0026__
