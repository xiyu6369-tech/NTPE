# TE v4.0 Stage-4.0.3 Adaptive Chunk Split Planner

Adds a pure chunk split planner for retry-time recovery.

The planner consumes an AdaptiveRetryPolicy decision and returns:
- whether splitting is required
- effective chunk size
- ordered segment boundaries
- optional overlap
- deterministic merge strategy

This stage does not modify Translation Runtime and does not execute translation.

## Validation

```powershell
python tools\apply_stage_403.py
python ntpe_te_v40_stage401_translation_reliability_baseline_test.py
python ntpe_te_v40_stage402_adaptive_retry_policy_test.py
python ntpe_te_v40_stage403_adaptive_chunk_split_planner_test.py
python -m pytest tests\integration\translation_reliability_stage401_baseline_test.py tests\integration\translation_reliability_stage402_adaptive_retry_policy_test.py tests\integration\translation_reliability_stage403_adaptive_chunk_split_planner_test.py -q
python ntpe_validate.py
```
