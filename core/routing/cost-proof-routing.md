# Cost and Token Proof Routing 0.5

Delegation is an economic and quality hypothesis. The comparison baseline remains pinned Sonnet 5 direct so benchmark cohorts stay comparable across topologies.

## Whole-tree candidate

Account separately for every active component: Lean root Sonnet executive, Haiku worker, Sonnet lead, Sonnet independent verifier, Opus executive, cache reads/writes, Batch lane, expected retries, and expected escalation to the direct fallback. Configured model aliases are resolved by the runtime; accepted configuration is never decorative.

`lean` requires explicit non-zero Sonnet executive usage before a delegated candidate can support an economic claim. A non-Sonnet Lean executive is a topology error. `opus-sonnet` requires non-zero Opus executive and Sonnet lead forecasts and rejects hidden Haiku usage. `frontier` requires non-zero Opus executive, Sonnet lead, and Haiku worker forecasts; omitting any tier invalidates the candidate.

The root Lean executive is startup/orchestration overhead, not a bounded worker retry. Do not multiply that root component by a worker retry probability unless the root session is actually replayed.

## Separate efficiency dimensions

API-equivalent USD, whole-tree provider tokens, root/main-model tokens, normalized payload bytes, and handoff overhead are separate measurements. A cheaper model may clear the cost gate while failing token efficiency.

The initial 0.5 token thresholds are calibration seeds and run in shadow mode by default:

```text
minimum_total_token_savings = 0.05
minimum_main_token_savings  = 0.15
```

They become rejection gates only through explicit opt-in and should be promoted to recommended policy only for calibrated benchmark buckets.

## Conservative gate

Delegate only when the candidate:

1. is permitted by criticality and independent verification;
2. stays below escalation, reread, forecast run-budget, and calibration limits;
3. has the runtime capabilities required by strict mode;
4. clears `minimumSavingsMargin` against the pinned direct baseline;
5. reports token-gate status separately, even when token enforcement remains shadow-only.

A route whose DreamTeam forecast cannot fit the configured run budget is `BLOCKED` or falls back to an allowed direct baseline according to ownership. The bundled Claude adapter currently reserves forecast cost; without authoritative provider usage reconciliation this is not a provider-side spending hard cap.

Rejected candidates preserve their forecast for audit.

## Profiles

Profile defaults are executable. Explicit configuration values override a profile, while omitted routing and budget values inherit its preset.

## Batch

Batch is eligible only when context is closed, retention is confirmed, project config opts in, and a real Batch executor is available. Interactive subagents are never priced as Batch.

## Calibration and claims

Enforcement and publication are bucket-specific by role, archetype, criticality, size, effort, cache mode, topology, and adapter version.

Cost publication requires paired quality parity, recomputed API-equivalent cost, configured median margin, positive lower-tail savings, and minimum samples in every reported bucket.

Token publication additionally requires configured median whole-tree and main-token savings plus positive lower-tail savings for both dimensions. Normalized payload claims require complete sidecar measurements. Forecast routing always keeps empirical savings claims disabled until paired provider evidence passes the applicable gates.
