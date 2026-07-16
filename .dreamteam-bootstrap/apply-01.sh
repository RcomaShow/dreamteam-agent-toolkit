#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT"

mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/skills/review/SKILL.md')"
cat > 'adapters/claude-code/plugins/dreamteam/skills/review/SKILL.md' <<'__DT_V03_0010__'
---
name: review
description: Review DreamTeam 0.3 routes, source anchors, runtime ledger, ownership, independent gates, and USD accounting without reproducing delegated work.
argument-hint: "[optional scope]"
disable-model-invocation: true
---

# DreamTeam Review 0.3

Scope: `$ARGUMENTS`

1. Read the route packet, topology, DCP/2 contracts, CHP/2 handoffs, checkpoints, and ledger summary.
2. Validate every FACT source with `protocol_v2.py --require-anchors`; verify current file anchors before a decision consumes them.
3. Reject unsupported facts, missing deduction evidence, hidden assumptions, stale blobs, unresolved handoffs, false verification claims, model contamination, and unaccountable benchmark reads.
4. Confirm route, criticality, root/lead/worker ownership, and the USD break-even decision remain valid after actual retries or scope changes.
5. Inspect all C3/public/consequential hunks directly. For M0/L1, use diff invariants, anchored sampling, compilation, and targeted tests instead of rereading full files.
6. Enforce verification timing: M0 gate-final, L1 branch review and targeted tests, L2 at decision points, C3 root direct.
7. Confirm the final oracle is independent from the authoring chain. Treat newly authored tests as evidence, not sole approval.
8. Confirm one active owner per code region, no overlapping worker question, no out-of-scope edit, and no successful checkpoint was needlessly rerun.
9. Report `SCOPED`, `IMPLEMENTED`, `COMPILED`, `TESTED`, `REVIEWED`, and `VERIFIED` only when achieved. Report measured USD separately from estimates and API-equivalent USD separately from invoice USD.
__DT_V03_0010__
mkdir -p "$(dirname -- 'adapters/claude-code/plugins/dreamteam/skills/run/SKILL.md')"
cat > 'adapters/claude-code/plugins/dreamteam/skills/run/SKILL.md' <<'__DT_V03_0011__'
---
name: run
description: Execute an engineering task through the USD-aware DreamTeam 0.3 control plane using Sonnet-Haiku or Opus-Sonnet-Haiku while preserving root ownership and quality parity.
argument-hint: "profile=<economy|balanced|offload|quality|cost-proof> topology=<sonnet-haiku|opus-sonnet-haiku> <task>"
disable-model-invocation: true
---

# DreamTeam Run 0.3

Task: `$ARGUMENTS`

You are the root orchestrator and final owner. Agents never delegate; every transition returns to you.

1. Read `${CLAUDE_SKILL_DIR}/references/constitution-kernel.md` and load `dreamteam.config.json`, defaulting to `cost-proof` and `sonnet-haiku` when absent.
2. Run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_cli.py" doctor .`. In enforced or benchmark mode, stop on a model override, invalid catalog, wrong root model, or disabled hook runtime.
3. Classify every code region as `M0`, `L1`, `L2`, or `C3`; apply consequential hard gates before cost estimation.
4. Build a small deterministic repo map before broad reading:
   `python3 "${CLAUDE_PLUGIN_ROOT}/bin/dreamteam_cli.py" repo-map . --tokens <configured-budget> --identifier <named-concept>`.
5. Emit a route packet and a work DAG. Parallel nodes must have different questions and non-conflicting write ownership. Validate waves with the bundled `schedule` command. Reuse completed checkpoints instead of rerunning successful nodes.
6. Price direct and delegated plans with full model IDs and fresh/cache/output/batch buckets. Include instructions, handoff, root verification, retries, escalation, and tool charges. Run the `route` command. In shadow mode execute direct while recording the recommendation; in enforce mode delegate only when the conservative 30-percent USD margin and quality parity pass.
7. For `sonnet-haiku`: Sonnet owns unresolved L2, all C3, and final gates; Haiku handles eligible discovery, M0, and closed L1.
8. For `opus-sonnet-haiku`: Opus owns ambiguity, architecture, all C3, and release; Sonnet lead agents handle root-bounded L2 and independent verification; Haiku handles eligible volume, M0, and closed L1. Cross-model escalation starts a new agent from validated anchors; same-model continuation resumes the previous agent.
9. Before every agent issue DCP/2 with closed paths/symbols, authoritative `K` decisions, reserved `R` decisions, verification, and budgets. Require CHP/2 facts to use file/cmd/record anchors.
10. Let independent read-only nodes run in one bounded wave when the scheduler approves. Never overlap workers on the same question or write region.
11. Use Message Batch only for immutable closed-context tasks, only when enabled and source-retention acknowledgment is true. Interactive repository discovery remains a Claude Code tool loop.
12. Record node checkpoints after each result. Verify anchors, contradictions, consequential regions, and class-specific gates without reproducing a delegated investigation. Main rereads above the configured ratio require a decision/C3/gate permit.
13. M0 verifies gate-final; L1 verifies specification-to-branch mapping plus targeted tests; L2 verifies at every decision point; C3 is root direct. The authoring chain cannot be the sole final oracle.
14. Resolve every handoff and report actual USD-accounting status, route, model tiers, reread ratio, retries, gates, and any benchmark-invalidating condition. Never claim savings from estimates alone.

Load references only when needed:

- legacy routes: `${CLAUDE_SKILL_DIR}/references/routing-policy.md`
- 0.3 routes and domain lead: `${CLAUDE_SKILL_DIR}/references/routes-v3.md`
- USD gate and runtime ledger: `${CLAUDE_SKILL_DIR}/references/cost-control.md`
- topologies: `${CLAUDE_SKILL_DIR}/references/topologies.md`
- workers: `${CLAUDE_SKILL_DIR}/references/worker-catalog.md`
- Sonnet leads: `${CLAUDE_SKILL_DIR}/references/lead-catalog.md`
- protocols: `${CLAUDE_SKILL_DIR}/references/compact-protocol.md` and `${CLAUDE_SKILL_DIR}/references/anchors-v3.md`
- profiles: `${CLAUDE_SKILL_DIR}/references/profiles.md` and `${CLAUDE_SKILL_DIR}/references/cost-proof.md`
- verification: `${CLAUDE_SKILL_DIR}/references/quality-gates.md` and `${CLAUDE_SKILL_DIR}/references/verification-v3.md`
__DT_V03_0011__
mkdir -p "$(dirname -- 'core/pricing/anthropic-2026-07-16.json')"
cat > 'core/pricing/anthropic-2026-07-16.json' <<'__DT_V03_0012__'
{
  "schema_version": 1,
  "catalog_id": "anthropic-2026-07-16",
  "provider": "anthropic",
  "currency": "USD",
  "effective_from": "2026-07-16",
  "effective_until": "2026-08-31",
  "source": {
    "checked_at": "2026-07-16",
    "description": "Anthropic Claude API pricing; Sonnet 5 introductory pricing window"
  },
  "models": {
    "claude-opus-4-8": {
      "aliases": ["opus", "opus-4.8"],
      "input_per_mtok": 5.0,
      "output_per_mtok": 25.0,
      "cache_write_5m_per_mtok": 6.25,
      "cache_write_1h_per_mtok": 10.0,
      "cache_read_per_mtok": 0.5,
      "batch_discount": 0.5,
      "tokenizer_multiplier": 1.3,
      "tool_prompt_tokens": {"none": 290, "auto": 290, "any": 410, "tool": 410}
    },
    "claude-sonnet-5": {
      "aliases": ["sonnet", "sonnet-5"],
      "input_per_mtok": 2.0,
      "output_per_mtok": 10.0,
      "cache_write_5m_per_mtok": 2.5,
      "cache_write_1h_per_mtok": 4.0,
      "cache_read_per_mtok": 0.2,
      "batch_discount": 0.5,
      "tokenizer_multiplier": 1.3,
      "tool_prompt_tokens": {"none": 354, "auto": 354, "any": 474, "tool": 474}
    },
    "claude-haiku-4-5": {
      "aliases": ["haiku", "haiku-4.5"],
      "input_per_mtok": 1.0,
      "output_per_mtok": 5.0,
      "cache_write_5m_per_mtok": 1.25,
      "cache_write_1h_per_mtok": 2.0,
      "cache_read_per_mtok": 0.1,
      "batch_discount": 0.5,
      "tokenizer_multiplier": 1.0,
      "tool_prompt_tokens": {"none": 496, "auto": 496, "any": 588, "tool": 588}
    }
  }
}
__DT_V03_0012__
mkdir -p "$(dirname -- 'core/pricing/anthropic-2026-09-01.json')"
cat > 'core/pricing/anthropic-2026-09-01.json' <<'__DT_V03_0013__'
{
  "schema_version": 1,
  "catalog_id": "anthropic-2026-09-01",
  "provider": "anthropic",
  "currency": "USD",
  "effective_from": "2026-09-01",
  "effective_until": null,
  "source": {
    "checked_at": "2026-07-16",
    "description": "Anthropic Claude API pricing after the Sonnet 5 introductory window"
  },
  "models": {
    "claude-opus-4-8": {
      "aliases": ["opus", "opus-4.8"],
      "input_per_mtok": 5.0,
      "output_per_mtok": 25.0,
      "cache_write_5m_per_mtok": 6.25,
      "cache_write_1h_per_mtok": 10.0,
      "cache_read_per_mtok": 0.5,
      "batch_discount": 0.5,
      "tokenizer_multiplier": 1.3,
      "tool_prompt_tokens": {"none": 290, "auto": 290, "any": 410, "tool": 410}
    },
    "claude-sonnet-5": {
      "aliases": ["sonnet", "sonnet-5"],
      "input_per_mtok": 3.0,
      "output_per_mtok": 15.0,
      "cache_write_5m_per_mtok": 3.75,
      "cache_write_1h_per_mtok": 6.0,
      "cache_read_per_mtok": 0.3,
      "batch_discount": 0.5,
      "tokenizer_multiplier": 1.3,
      "tool_prompt_tokens": {"none": 354, "auto": 354, "any": 474, "tool": 474}
    },
    "claude-haiku-4-5": {
      "aliases": ["haiku", "haiku-4.5"],
      "input_per_mtok": 1.0,
      "output_per_mtok": 5.0,
      "cache_write_5m_per_mtok": 1.25,
      "cache_write_1h_per_mtok": 2.0,
      "cache_read_per_mtok": 0.1,
      "batch_discount": 0.5,
      "tokenizer_multiplier": 1.0,
      "tool_prompt_tokens": {"none": 496, "auto": 496, "any": 588, "tool": 588}
    }
  }
}
__DT_V03_0013__
mkdir -p "$(dirname -- 'core/profiles/cost-proof.md')"
cat > 'core/profiles/cost-proof.md' <<'__DT_V03_0014__'
# Cost-Proof Profile

Primary target: minimize **measured total USD** while maintaining the configured quality-parity floor.

```text
optimization_target=usd
routing_mode=shadow_until_confident
minimum_savings_margin=0.30
minimum_history_samples=5
max_main_reread_ratio=0.20
target_compression_ratio=8.0
max_active_workers=2
parallelism=independent_only
checkpoint_every_node=true
resume_completed_nodes=true
fact_anchors=required
independent_gate=true
batch=closed_context_opt_in
```

Hard gates override cost: C3 remains root-owned; missing acceptance criteria, ambiguous semantics, unaccountable reads, or a verification chain that is not independent select direct/root review.

A route is promoted from shadow to enforced only when its task bucket has quality parity and a conservative saving of at least 30 percent. Negative-ROI demotion is scoped to the measured bucket, never to the worker globally.
__DT_V03_0014__
mkdir -p "$(dirname -- 'core/protocols/chp-2.md')"
cat > 'core/protocols/chp-2.md' <<'__DT_V03_0015__'
# Compact Handoff Protocol — CHP/2

Workers and leads return a decision-relevant delta, not a narrative recap.

```text
CHP|2
RUN|<run-id>
TASK|<task-id>
CONTRACT|<sha256 or UNAVAILABLE>
S|<DONE|PARTIAL|BLOCKED|FAILED>|<short reason>
E|<id>|FACT|<source anchor>|<claim>
E|<id>|DEDUCTION|<supporting ids>|<claim>
E|<id>|ASSUMPTION|<scope>|<claim>
E|<id>|UNKNOWN|<scope>|<claim>
C|<id>|<path#symbol>|<change>
H|<id>|<category>|<location>|<decision required>|<blocked work>
V|<id>|<PASS|FAIL|NR>|<check or command>|<result>
W|<id>|<risk>|<evidence>
N|<ORCHESTRATOR|WORKER:role>|<next action>
```

## Source anchors

Cost-proof FACT records use one of:

```text
file:<path>:L<start>-L<end>@blob:<git-oid>#sha256:<slice-sha256>
cmd:<command-id>#sha256:<normalized-output-sha256>
record:<protocol-or-ledger-id>
```

File anchors bind a claim to the exact file version and slice. A stale blob must be revalidated and returned as a new evidence record.

## Precision rules

- FACT requires direct anchored evidence.
- DEDUCTION cites existing evidence IDs.
- ASSUMPTION is allowed only when the contract permits it.
- UNKNOWN never silently becomes a fact.
- DONE means the worker contract is complete, not that the whole task is production-ready, and cannot include unresolved H records.
- PASS names the actual check; NR means not run.
- Do not repeat the contract, user request, or acknowledged records.
- Escape fields according to `escaping.md`.
__DT_V03_0015__
mkdir -p "$(dirname -- 'core/protocols/quality-gates.md')"
cat > 'core/protocols/quality-gates.md' <<'__DT_V03_0016__'
# Quality Gates 0.3

Use explicit states; never use `complete` as an unsupported quality claim.

```text
SCOPED       Contract, ownership, route, and boundaries are explicit
IMPLEMENTED  Requested edits exist
COMPILED     Targeted compilation passed
TESTED       Targeted tests passed
REVIEWED     Consequential changes and decisions were inspected by the required owner
VERIFIED     Independent acceptance or end-to-end gate passed
COSTED       Whole-route measured or explicitly estimated USD is recorded
```

A worker reports only gates it performed. Final success requires gates declared before delegation and an independent oracle outside the authoring chain.

| Work class | Default execution | Minimum final gate |
|---|---|---|
| M0 | Haiku | diff invariant + targeted deterministic check |
| L1 | Haiku when closed | behavior/branch review + targeted tests + anchor sampling |
| L2 | Sonnet root/lead or hybrid | verification at decision points + direct critical-region review |
| C3 | root | root direct implementation/review + required checks |
| discovery | Haiku/Sonnet lead | decision-critical anchors reviewed |
| failure triage | Haiku | corrective change independently verified |
__DT_V03_0016__
mkdir -p "$(dirname -- 'core/protocols/task-ledger.md')"
cat > 'core/protocols/task-ledger.md' <<'__DT_V03_0017__'
# Task Ledger Protocol — TLP/3

The runtime ledger is authoritative; this line-oriented view exposes only the state needed by the next model action.

```text
TLP|3
RUN|<run-id>|<topology>|<shadow|enforce>
TASK|<id>|<owner>|<PENDING|ACTIVE|DONE|BLOCKED>|<scope>
NODE|<id>|<dependencies>|<model-tier>|<interactive|batch|direct>|<status>
ROUTE|<task-id>|<route>|<M0|L1|L2|C3>|<bucket>|<reason>
COST|<task-id>|direct=<usd>;delegated=<usd>;margin=<ratio>;quality=<state>
DEC|<id>|<decision>|<evidence IDs>|<impact>
OPEN|<id>|<owner>|<required action>|<blocked task IDs>
CHK|<id>|<PASS|FAIL|NR>|<verification>
WORKER|<id>|<role>|<scope>|<ACTIVE|PAUSED|CLOSED>
READ|<owner>|<file anchor>|<DEEP|SHALLOW>|<INITIAL|VERIFY|DECISION|C3|GATE>
PERMIT|<id>|<reason>|<file span>|<OPEN|CONSUMED>
```

Rules:

- SQLite WAL events and checkpoints are append-only; this view replaces stale state rather than narrating history.
- Source records contain hashes and byte lengths, never source content.
- Completed nodes are resumed/skipped, not rerun.
- Parallel nodes require independent questions and non-conflicting write ownership.
- Cross-model escalation creates a new node from validated anchors.
__DT_V03_0017__
mkdir -p "$(dirname -- 'core/protocols/verification-policy-v3.md')"
cat > 'core/protocols/verification-policy-v3.md' <<'__DT_V03_0018__'
# Verification Policy 0.3

Verification is proportional to criticality and independent from authorship.

| Class | When verification occurs | Minimum independent evidence |
|---|---|---|
| M0 | gate-final | diff invariant plus targeted deterministic check |
| L1 | after the bounded implementation | specification-to-branch review plus targeted tests and anchor sampling |
| L2 | at every decision boundary before dependent work | direct review of decision-critical regions and tests |
| C3 | throughout root implementation/review | root direct review and every required acceptance gate |
| discovery | before a decision consumes the result | decision-critical anchors, contradictions, and material unknowns |

A worker may run pre-existing tests for feedback. Tests written by the same authoring chain are useful evidence but cannot be the only final oracle. An independent gate is one or more of:

- a pre-existing or hidden acceptance check;
- a separate verifier outside the authoring chain;
- root direct review of the relevant behavior;
- compiler, static analyzer, or deterministic invariant not authored by the chain.

Deferred verification stops at decision points, before long dependent chains, and whenever the proposed gate comes from the same chain that wrote the code.
__DT_V03_0018__
mkdir -p "$(dirname -- 'core/routing/cost-aware-routing.md')"
cat > 'core/routing/cost-aware-routing.md' <<'__DT_V03_0019__'
# USD-Aware Routing 0.3

## Canonical usage

Every model call is recorded by full model ID with mutually exclusive buckets:

```text
fresh_input_tokens
cache_write_5m_tokens
cache_write_1h_tokens
cache_read_tokens
output_tokens
server_tool_usd
requests
tool_calls
batch
```

Token counts are never compared across model families as if they were equal. Versioned pricing catalogs convert each model's measured usage to USD for the run date and can reprice historical runs under a later price epoch.

## Break-even gate

For direct plan `D` and delegated plan `H`:

```text
E[H] = normal_worker_and_main_cost
     + P(retry) * retry_cost
     + P(escalation) * escalation_cost
     + fixed_tool_cost

delegate only when
  upper_confidence(E[H]) <= (1 - margin) * lower_confidence(E[D])
  and quality(H) >= quality(D) - tolerance
```

The default margin is 30 percent. Cold-start estimates are conservative priors and operate in shadow mode. Enforcement requires enough paired history in the exact route bucket.

## Bucketed learning

History is keyed by worker, task kind, criticality, size, route, model, effort, cache mode, and adapter version. A negative result demotes only that bucket. For example, failure triage may remain profitable on a 50k-line cold log while being demoted on a small warm log.

## Hard gates

Cost cannot override:

- C3 or unresolved architecture/business semantics;
- missing acceptance criteria or closed ownership;
- a delegation contract comparable to the implementation;
- an expected root reread above the configured limit;
- unaccountable source reads in strict benchmark mode;
- a final gate produced only by the chain that authored the change.

## Shadow, enforce, demote

```text
INSUFFICIENT_DATA         -> shadow recommendation, execute direct
DELEGATE_ENFORCED         -> cost and quality confidence passed
MAIN_DIRECT_NEGATIVE_ROI  -> route bucket demoted
MAIN_DIRECT_QUALITY       -> route bucket demoted for quality
```
__DT_V03_0019__
