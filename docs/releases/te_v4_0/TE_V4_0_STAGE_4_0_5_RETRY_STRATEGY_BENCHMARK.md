# TE v4.0 Stage-4.0.5 Retry Strategy Benchmark

Compares fixed retry behavior with AdaptiveRetryPolicy and
AdaptiveChunkSplitPlanner using deterministic supplied cases.

The benchmark measures:
- success rate
- retry count
- estimated total time
- split recoveries
- provider rebuild recoveries

No real retry, sleep, provider request, HTTP request, or translation occurs.

## Validation

```powershell
python tools\apply_stage_405.py
python ntpe_te_v40_stage401_translation_reliability_baseline_test.py
python ntpe_te_v40_stage402_adaptive_retry_policy_test.py
python ntpe_te_v40_stage403_adaptive_chunk_split_planner_test.py
python ntpe_te_v40_stage404_translation_failure_analyzer_test.py
python ntpe_te_v40_stage405_retry_strategy_benchmark_test.py
python -m pytest tests\integration\translation_reliability_stage401_baseline_test.py tests\integration\translation_reliability_stage402_adaptive_retry_policy_test.py tests\integration\translation_reliability_stage403_adaptive_chunk_split_planner_test.py tests\integration\translation_reliability_stage404_failure_analyzer_test.py tests\integration\translation_reliability_stage405_retry_strategy_benchmark_test.py -q
python ntpe_validate.py
```
