# Economy Profile

Primary target: minimize total usage and delegation overhead.

```text
optimization_target=total_tokens
max_active_workers=1
max_worker_chain=1
max_worker_turns=6
max_deep_reads=6
max_output_records=16
max_retries=1
parallelism=off
orchestrator_verification=critical_evidence_diff_and_targeted_checks
```

Prefer MAIN_DIRECT for small tasks and a single worker only for clearly beneficial work.

# Balanced Profile

Default compromise between total cost, main-model conservation, and confidence.

```text
optimization_target=weighted_cost
max_active_workers=1
max_worker_chain=2
max_worker_turns=10
max_deep_reads=10
max_output_records=24
max_retries=1
parallelism=off
orchestrator_verification=critical_evidence_diff_and_targeted_checks
```

# Offload Profile

Primary target: reduce high-capability/main-model work while preserving verified quality.

```text
optimization_target=main_model_tokens
max_active_workers=1
max_worker_chain=3
max_worker_turns=10
max_deep_reads=12
max_output_records=28
max_retries=1
parallelism=off
nested_agents=off
prefer_worker_for_search=true
prefer_worker_for_logs=true
prefer_worker_for_scaffolding=true
prefer_worker_for_bounded_logic=true
prefer_worker_for_tests=true
prefer_worker_for_diff_classification=true
orchestrator_max_critical_references=4
orchestrator_avoid_duplicate_reads=true
```

C3 code remains orchestrator-owned in every profile.

# Quality Profile

Primary target: quality and risk reduction, while still avoiding unnecessary bulk work in the main context.

```text
optimization_target=quality
max_active_workers=1
max_worker_chain=3
max_worker_turns=14
max_deep_reads=16
max_output_records=36
max_retries=2
parallelism=off
high_capability_worker=allowed_when_explicitly_justified
orchestrator_verification=expanded
```
