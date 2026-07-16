# Economy Profile

Use when cost reduction is the primary objective and the task is well specified.

```text
max_active_workers=1
max_worker_turns=6
max_deep_reads=6
max_output_records=20
max_retries=1
parallelism=off
orchestrator_verification=critical_evidence_and_diff
```

Escalate early. Do not trade correctness for a forced worker completion.

# Balanced Profile

Default profile for normal engineering work.

```text
max_active_workers=1
max_worker_turns=10
max_deep_reads=10
max_output_records=35
max_retries=2
parallelism=off
orchestrator_verification=critical_evidence_diff_and_targeted_checks
```

# Quality Profile

Use for broader verification or high-impact work. Critical decisions still remain with the orchestrator.

```text
max_active_workers=2
max_worker_turns=14
max_deep_reads=16
max_output_records=50
max_retries=2
parallelism=independent_scopes_only
orchestrator_verification=all_decision_evidence_diff_and_acceptance_checks
```
