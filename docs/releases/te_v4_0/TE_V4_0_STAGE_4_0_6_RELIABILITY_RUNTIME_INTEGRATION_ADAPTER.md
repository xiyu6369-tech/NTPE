# TE v4.0 Stage-4.0.6 Reliability Runtime Integration Adapter

Adds a disabled-by-default, analysis-only adapter.

It maps caller-supplied runtime metadata into:
- reliability baseline report
- failure analysis
- retry decisions
- chunk split plans

It does not execute retries, chunk splits, provider calls, HTTP calls, or real
translation. Source and translated text are converted to lengths and discarded.

## Validation

```powershell
python tools\apply_stage_406.py
python ntpe_te_v40_stage401_translation_reliability_baseline_test.py
python ntpe_te_v40_stage402_adaptive_retry_policy_test.py
python ntpe_te_v40_stage403_adaptive_chunk_split_planner_test.py
python ntpe_te_v40_stage404_translation_failure_analyzer_test.py
python ntpe_te_v40_stage405_retry_strategy_benchmark_test.py
python ntpe_te_v40_stage406_reliability_runtime_integration_adapter_test.py
python -m pytest tests\integration\translation_reliability_stage401_baseline_test.py tests\integration\translation_reliability_stage402_adaptive_retry_policy_test.py tests\integration\translation_reliability_stage403_adaptive_chunk_split_planner_test.py tests\integration\translation_reliability_stage404_failure_analyzer_test.py tests\integration\translation_reliability_stage405_retry_strategy_benchmark_test.py tests\integration\translation_reliability_stage406_runtime_integration_adapter_test.py -q
python ntpe_validate.py
```
