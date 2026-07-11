# TE v4.0 Stage-4.0.4 Translation Failure Analyzer

Converts Translation Reliability reports into:
- ranked failure causes
- severity and impact scores
- priority repair actions
- retry and latency diagnostics

This stage does not modify Runtime or Provider behavior.

## Validation

```powershell
python tools\apply_stage_404.py
python ntpe_te_v40_stage401_translation_reliability_baseline_test.py
python ntpe_te_v40_stage402_adaptive_retry_policy_test.py
python ntpe_te_v40_stage403_adaptive_chunk_split_planner_test.py
python ntpe_te_v40_stage404_translation_failure_analyzer_test.py
python -m pytest tests\integration\translation_reliability_stage401_baseline_test.py tests\integration\translation_reliability_stage402_adaptive_retry_policy_test.py tests\integration\translation_reliability_stage403_adaptive_chunk_split_planner_test.py tests\integration\translation_reliability_stage404_failure_analyzer_test.py -q
python ntpe_validate.py
```
