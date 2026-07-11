# TE v5.3.1 Unified Quality Gate

## Scope

TE v5.3.1 unifies the TE v5 quality analysis and the established Runtime QA
result after both systems have evaluated the same normalized provider output.
It is an additive integration stage and does not add provider calls or semantic
rewriting.

## Runtime flow

```text
provider output
  -> existing cleanup and locked-term handling
  -> TE v5 Phase 1 safe normalization and analysis
  -> Legacy Runtime QA analysis
  -> issue normalization and cross-system deduplication
  -> unified score and decision
  -> retry / accepted_with_warnings / accepted / reject
  -> optional per-attempt JSON report
```

## Unified contract

The authoritative report fields use schema version `5.3.1` and include:

- `quality_v5_issues`
- `legacy_qa_issues`
- `merged_issues`
- `normalizations`
- `score`
- `decision`
- `retry_required`
- `final_reason`
- `attempt`
- `chunk_id`

Supported decisions are `accepted`, `accepted_with_warnings`,
`retry_required`, `rejected`, and `runtime_error`. A score of 100 is only
possible when `merged_issues` is empty.

## Compatibility

Existing TE v5 Phase 1 report fields remain present, including
`quality_score`, `issues`, `quality_result`, and the repair pipeline details.
The new unified `score` and `decision` fields are authoritative for Runtime
behavior. The public `merge_quality_v5_into_runtime_qa()` function remains
available and now delegates to the unified gate.

`--no-quality-v5` continues to disable TE v5 analysis while Legacy QA remains
active. `--no-quality-v5-report` suppresses JSON output without disabling the
gate decision.

## Safety boundary

This stage does not change provider timeout, retry, NVIDIA 40 RPM throttling,
503 backpressure, resume, output merging, or CLI defaults. It does not call a
provider from quality code and does not perform high-risk semantic repairs.

## Validation

```text
python ntpe_te_v531_unified_quality_gate_test.py
python ntpe_te_v530_quality_runtime_integration_phase1_test.py
python ntpe_te_v523_provider_backpressure_resume_test.py
python ntpe_te_v30_stage022_runtime_speed_policy_test.py
python ntpe_validate.py
```
