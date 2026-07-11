# TE v4.1 Stage-4.1.3 Recovery Outcome Guard

Validates recovery output before it can be accepted.

Checks:
- empty output
- too-short / too-long output
- Hangul residue
- duplicate lines
- recovery success flag
- final recovery outcome

No provider, HTTP, API key, Runtime, launcher, or real translation side effect.

## Validation

```powershell
python tools\apply_stage_413.py
python ntpe_te_v41_stage411_adaptive_retry_execution_harness_test.py
python ntpe_te_v41_stage412_runtime_recovery_hook_adapter_test.py
python ntpe_te_v41_stage413_recovery_outcome_guard_test.py
python -m pytest tests\integration\translation_reliability_stage411_adaptive_retry_execution_harness_test.py tests\integration\translation_reliability_stage412_runtime_recovery_hook_adapter_test.py tests\integration\translation_reliability_stage413_recovery_outcome_guard_test.py -q
python ntpe_validate.py
```
