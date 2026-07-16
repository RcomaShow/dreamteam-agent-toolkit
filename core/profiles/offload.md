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
