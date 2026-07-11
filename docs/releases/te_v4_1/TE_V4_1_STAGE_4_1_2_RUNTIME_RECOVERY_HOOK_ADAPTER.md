# TE v4.1 Stage-4.1.2 Runtime Recovery Hook Adapter

Adds an opt-in Runtime-facing adapter around the isolated retry harness.

The adapter:
- is disabled by default
- accepts only `translation_runtime` as caller
- requires a runtime_id and injected handler
- delegates bounded recovery to AdaptiveRetryExecutionHarness
- does not retain source or translated text
- does not modify Translation Runtime or Provider Runtime

## Validation

```powershell
python tools\apply_stage_412.py
python ntpe_te_v41_stage411_adaptive_retry_execution_harness_test.py
python ntpe_te_v41_stage412_runtime_recovery_hook_adapter_test.py
python -m pytest tests\integration\translation_reliability_stage411_adaptive_retry_execution_harness_test.py tests\integration\translation_reliability_stage412_runtime_recovery_hook_adapter_test.py -q
python ntpe_validate.py
```
