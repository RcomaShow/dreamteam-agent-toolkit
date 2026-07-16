#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

mkdir -p "$(dirname -- 'core/topologies/opus-sonnet-haiku.md')"
cat > 'core/topologies/opus-sonnet-haiku.md' <<'__DT_V03_0027__'
# Topology: Opus → Sonnet → Haiku

Use this topology when Opus quality is required for consequential ownership but it would be wasteful for Opus to perform all domain reasoning and volume work.

```text
OPUS ROOT
  owns requirements, architecture, ambiguity, C3, release decision
  |
  +-- SONNET DOMAIN LEAD
  |     bounded L2 analysis/implementation from authoritative Opus decisions
  |     independent verification outside the authoring chain
  |
  +-- HAIKU WORKERS
        discovery volume, M0, closed L1, routine verification evidence
```

The hierarchy is logical, while dispatch remains a star: only Opus/root opens DCP/2 contracts and transitions ownership. Sonnet cannot create Haiku workers autonomously. This avoids hidden chains, makes every handoff billable, and preserves one active owner per code region.

## Escalation and resume

- Same model, same goal, same ownership: resume the prior agent checkpoint.
- Haiku → Sonnet or Sonnet → Opus: start a new agent from validated source anchors and completed-node checkpoints.
- Never attempt an undocumented live model swap inside the same agent history.
- Successful independent nodes are retained when another node fails; retry only the failed node.

## Ownership

| Class | Default execution | Required final owner |
|---|---|---|
| M0 | Haiku | Sonnet/Opus proportional gate |
| L1 | Haiku when fully specified | Sonnet or Opus gate |
| L2 | Sonnet domain lead, optionally with Haiku pieces | Opus decision ownership |
| C3 | Opus direct | Opus direct |

The topology is benchmarked against both Opus-only (`root-direct`) and Sonnet-5-only baselines. Claims must name the baseline; a cheaper Opus-quality cascade and a cheaper Sonnet-quality cascade are different results.
__DT_V03_0027__
mkdir -p "$(dirname -- 'core/topologies/sonnet-haiku.md')"
cat > 'core/topologies/sonnet-haiku.md' <<'__DT_V03_0028__'
# Topology: Sonnet → Haiku

Use this topology when Sonnet 5 is the final orchestrator and the target is to beat an equivalent cached Sonnet-5-only run in total USD without lowering acceptance quality.

```text
SONNET ROOT
  owns requirements, architecture, unresolved L2, all C3, final gates
  |
  +-- HAIKU DISCOVERY   read-only volume, repo map deltas, logs, diff classification
  +-- HAIKU EXECUTION   M0 and completely specified L1
  +-- HAIKU VERIFICATION routine bounded evidence, never final self-approval
```

The graph is root-controlled. Haiku workers never delegate and never decide public or consequential semantics. Independent tasks may run in the same wave only after the scheduler proves distinct questions and non-conflicting write ownership.

## Cost gate

A route is eligible only when:

```text
UCB(expected_hybrid_usd) <= 0.70 * LCB(expected_direct_usd)
quality_hybrid >= quality_direct - tolerance
```

Expected hybrid cost includes worker instructions, fresh/cache input, output, handoff, root verification, tool charges, retry probability, and escalation probability. Warm Sonnet cache is modeled explicitly; material already cheap in the root context is not offloaded merely because Haiku has a lower base price.

## Best initial candidates

- large symbol/repository discovery with a small anchored handoff;
- very large logs reduced to one causal chain;
- high-volume mechanical edits and scaffolding;
- large mostly-mechanical diffs classified before root review;
- repetitive documentation and test generation from a closed matrix.

Small, warm, decision-dense work remains `MAIN_DIRECT` until measurement proves otherwise.
__DT_V03_0028__
mkdir -p "$(dirname -- 'docs/v0.3-design.md')"
cat > 'docs/v0.3-design.md' <<'__DT_V03_0029__'
# DreamTeam 0.3 Design — Cost Proof and Cascades

## Mission

Deliver root-model quality with lower measured total cost than an equivalent single-model run. Token reduction is an implementation technique; USD at quality parity is the objective.

## Why 0.2 was insufficient

Version 0.2 defined strong ownership and handoff policy, but its compression and reread targets were advisory. It had no pricing epoch, whole-tree usage schema, runtime read enforcement, checkpoint store, or paired quality/cost evidence. Version 0.3 makes those mechanisms executable.

## Architecture

```text
Claude Code skill / other adapter
        |
        v
preflight -> classify -> deterministic repo map -> USD gate
        |                                      |
        | direct                               | delegated
        v                                      v
root work                         root-controlled DAG waves
                                            /       \
                                      lead nodes   worker nodes
                                            \       /
                                   anchored handoffs/checkpoints
                                                |
                                     independent class gate
                                                |
                                   usage + reads + outcome ledger
```

The runtime is standard-library Python. SQLite WAL is the only state engine. The plugin bundles the same runtime files and versioned pricing catalogs used by repository-local tooling.

## Two cascades

`sonnet-haiku` optimizes against Sonnet-5-only. `opus-sonnet-haiku` preserves Opus ownership while moving bounded L2 to Sonnet and volume to Haiku. The latter is logically hierarchical but operationally root-controlled: only Opus dispatches, preventing invisible nested-agent cost and ownership drift.

## Cost model

Each call records fresh input, cache writes by TTL, cache reads, output, server-tool USD, request count, tool calls, and Batch status. Costs are calculated by full model ID and effective-date catalog. Raw usage is retained so a run can be repriced after a list-price change.

The gate uses conservative direct and delegated bounds. Delegated expected cost includes retries and escalation. Quality is a hard constraint, not a term that can be traded away for cost.

## Read accounting

A source read is tied to repository-relative path, git-compatible blob OID, line interval, slice SHA-256, and per-line byte lengths. Reread overlap is computed on unique source bytes, avoiding tokenizer distortion between Haiku, Sonnet, and Opus. Plugin hooks warn, ask, or deny before the root exceeds its ratio. Explicit permits keep consequential rereads safe and auditable.

## Context reduction

Three deterministic layers precede LLM summarization:

1. a graph-ranked repo map within a hard token budget;
2. clipping and hashing of verbose tool output;
3. an append-only head/summary/tail view that preserves pinned decisions, contracts, anchors, gates, recent events, and atomic tool-call groups.

Condensation uses soft and hard thresholds plus a polling interval so frequent summaries do not continuously invalidate prompt caches.

## Resume and parallelism

The work graph validates dependencies, criticality, ownership, semantic-question duplication, and write overlap. A wave can dispatch independent nodes in parallel after reserving their conservative USD budget. Checkpoints are append-only. On failure, successful sibling nodes remain completed and only the failed node is retried.

Same-model continuation resumes prior state. Cross-model escalation starts a new agent from validated anchors and completed checkpoints rather than attempting an undocumented model swap inside one history.

## Verification

Verification timing follows criticality. The authoring chain cannot provide the sole final oracle. A Sonnet independent verifier is available under an Opus root; the root still owns the release decision.

## Benchmark design

Pairs share commit, prompt, acceptance hash, cache mode, billing surface, and tool permissions. The direct arm forbids agents. The hybrid arm permits only topology models. Whole-tree usage, retries, escalation, corrections, and final gates are included. A bucket is promoted only after sufficient paired samples and a conservative 30-percent saving at the quality floor.

## External design review

The 0.3 design inspected mature open-source orchestration systems and adopted narrow patterns rather than dependencies:

- LangGraph: durable checkpoints, thread identity, and preservation of successful parallel writes;
- Aider: deterministic symbol maps, reference-graph ranking, cache, and exact token budgeting;
- OpenHands SDK: append-only condensation records and soft/hard context triggers;
- SWE-agent: cache-aware history polling, stale-window removal, and bounded observations;
- AutoGen: composable termination conditions and head/tail token-limited contexts;
- RouteLLM: shadow evaluation and threshold calibration on representative traffic;
- PydanticAI: canonical cache-aware usage fields and pre/post usage limits;
- LiteLLM: budget filters and scoped spend windows;
- CrewAI: explicit manager tier and opt-in tool-result cache safety.

No framework code is vendored and none is required at runtime. DreamTeam combines the patterns around source-code ownership, USD break-even, and independent engineering gates.

## Claims

0.3 provides the implementation and methodology. It does not claim a measured saving until representative paired runs are published.
__DT_V03_0029__
mkdir -p "$(dirname -- 'dreamteam.config.example.json')"
cat > 'dreamteam.config.example.json' <<'__DT_V03_0030__'
{
  "version": 2,
  "constitution": "DT-C1",
  "profile": "cost-proof",
  "topology": "sonnet-haiku",
  "models": {
    "root": "claude-sonnet-5",
    "lead": null,
    "worker": "claude-haiku-4-5",
    "effort": {"root": "high", "worker": "low"}
  },
  "pricing": {
    "provider": "anthropic",
    "catalogDir": "core/pricing",
    "catalog": null,
    "currency": "USD",
    "billingSurface": "api"
  },
  "routing": {
    "objective": "usd",
    "decisionMode": "shadow",
    "minimumSavingsMargin": 0.3,
    "qualityTolerance": 0.0,
    "minimumQuality": 0.95,
    "confidenceBuffer": 0.1,
    "minimumHistorySamples": 5,
    "minimumHistoryQualityPassRate": 0.95,
    "targetCompressionRatio": 8.0,
    "maxMainRereadRatio": 0.2,
    "directMaxLocalFiles": 2,
    "maxActiveWorkers": 2,
    "allowParallelIndependent": true,
    "autoDemoteNegativeRoi": true,
    "bucketDimensions": ["worker", "taskKind", "criticality", "size", "cacheMode"]
  },
  "runtime": {
    "ledgerPath": ".dreamteam/ledger.sqlite3",
    "enforceReadLedger": true,
    "rereadEnforcementAction": "ask",
    "requireFactAnchors": true,
    "verifyAnchors": true,
    "checkpointEveryNode": true,
    "resumeCompletedNodes": true,
    "storeSourceContent": false
  },
  "context": {
    "strategy": "head-summary-tail",
    "repoMapTokens": 2048,
    "maxTokens": 80000,
    "softTriggerRatio": 0.75,
    "targetRatio": 0.45,
    "keepFirst": 2,
    "keepLast": 12,
    "pollingEvents": 4,
    "minimumProgress": 0.1,
    "clipToolOutputCharacters": 100000,
    "pinTags": ["decision", "contract", "anchor", "gate"]
  },
  "verification": {
    "independentGateRequired": true,
    "M0": "gate-final",
    "L1": "spec-branch-review-and-targeted-tests",
    "L2": "verify-at-decision-points",
    "C3": "root-direct-review",
    "requireTargetedTest": true,
    "allowFullSuite": "root-only"
  },
  "batch": {
    "enabled": false,
    "closedContextOnly": true,
    "sourceRetentionAcknowledged": false,
    "allowedRoles": ["context-synthesizer", "diff-auditor", "test-gap-finder"]
  },
  "benchmark": {
    "strictToolAccounting": true,
    "paired": true,
    "baseline": "sonnet-5-direct",
    "randomizeArmOrder": true,
    "cacheModes": ["cold", "warm-main"],
    "publishMeasuredOnly": true
  },
  "budgets": {
    "maxRunUsd": null,
    "maxRequests": 50,
    "maxToolCalls": 200,
    "maxInputTokens": null,
    "maxOutputTokens": null,
    "maxWorkerTurns": 10,
    "maxWorkerChain": 3,
    "maxRetries": 1
  },
  "telemetry": {"enabled": false, "storeSourceContent": false}
}
__DT_V03_0030__
mkdir -p "$(dirname -- 'dreamteam_runtime/__init__.py')"
cat > 'dreamteam_runtime/__init__.py' <<'__DT_V03_0031__'
"""DreamTeam 0.3 dependency-free orchestration runtime."""

from .budget import BudgetLimits, BudgetState
from .pricing import PricingCatalog, Usage
from .routing import BreakEvenPolicy, PlanEstimate, Route, Topology, WorkSignals
from .scheduler import WorkGraph, WorkNode

__all__ = [
    "BreakEvenPolicy",
    "BudgetLimits",
    "BudgetState",
    "PlanEstimate",
    "PricingCatalog",
    "Route",
    "Topology",
    "Usage",
    "WorkGraph",
    "WorkNode",
    "WorkSignals",
]

__version__ = "0.3.0"
__DT_V03_0031__
mkdir -p "$(dirname -- 'dreamteam_runtime/batch.py')"
cat > 'dreamteam_runtime/batch.py' <<'__DT_V03_0032__'
"""Closed-context Anthropic Message Batch manifest support.

Batch is deliberately isolated from interactive Claude Code subagents.  Only tasks
with immutable, source-hashed context may enter this lane.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import urllib.error
import urllib.request


class BatchError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BatchTask:
    custom_id: str
    system: str
    prompt: str
    source_hash: str
    max_tokens: int = 1_024
    metadata: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "BatchTask":
        required = {"custom_id", "prompt", "source_hash"}
        missing = required - set(value)
        if missing:
            raise BatchError(f"missing batch fields: {sorted(missing)}")
        source_hash = str(value["source_hash"])
        if len(source_hash) != 64 or any(char not in "0123456789abcdef" for char in source_hash):
            raise BatchError("source_hash must be lowercase SHA-256")
        max_tokens = int(value.get("max_tokens", 1024))
        if max_tokens < 1:
            raise BatchError("max_tokens must be positive")
        return cls(
            custom_id=str(value["custom_id"]),
            system=str(value.get("system", "")),
            prompt=str(value["prompt"]),
            source_hash=source_hash,
            max_tokens=max_tokens,
            metadata=value.get("metadata"),
        )


def hash_closed_context(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return sha256(data).hexdigest()


def build_manifest(
    tasks: Sequence[BatchTask],
    *,
    model: str = "claude-haiku-4-5",
    source_retention_acknowledged: bool = False,
) -> dict[str, Any]:
    if not source_retention_acknowledged:
        raise BatchError(
            "Batch source retention must be explicitly acknowledged before building a manifest"
        )
    if len({task.custom_id for task in tasks}) != len(tasks):
        raise BatchError("batch custom_id values must be unique")
    requests = []
    for task in tasks:
        params: dict[str, Any] = {
            "model": model,
            "max_tokens": task.max_tokens,
            "messages": [{"role": "user", "content": task.prompt}],
            "metadata": {
                "user_id": f"dreamteam:{task.source_hash[:24]}",
            },
        }
        if task.system:
            params["system"] = task.system
        requests.append(
            {
                "custom_id": task.custom_id,
                "params": params,
                "dreamteam": {
                    "source_hash": task.source_hash,
                    "closed_context": True,
                    "metadata": task.metadata or {},
                },
            }
        )
    return {
        "schema_version": 1,
        "provider": "anthropic",
        "model": model,
        "source_retention_acknowledged": True,
        "requests": requests,
    }


def anthropic_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "requests": [
            {"custom_id": request["custom_id"], "params": request["params"]}
            for request in manifest.get("requests", [])
        ]
    }


def submit_manifest(
    manifest: Mapping[str, Any],
    *,
    api_key: str | None = None,
    endpoint: str = "https://api.anthropic.com/v1/messages/batches",
    timeout: int = 60,
) -> dict[str, Any]:
    """Submit a manifest when explicitly invoked by a user-controlled CLI.

    The library never submits automatically.  The API key is read only at call time
    and is never persisted in the ledger or manifest.
    """

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise BatchError("ANTHROPIC_API_KEY is required for submission")
    data = json.dumps(anthropic_payload(manifest)).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise BatchError(f"batch submission failed: {exc}") from exc


def load_tasks(path: str | Path) -> list[BatchTask]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    values = data if isinstance(data, list) else data.get("tasks", [])
    return [BatchTask.from_mapping(value) for value in values]
__DT_V03_0032__
