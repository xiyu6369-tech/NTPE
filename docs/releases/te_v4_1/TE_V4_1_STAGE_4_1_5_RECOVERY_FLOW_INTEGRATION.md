# TE v4.1 Stage-4.1.5 Recovery Flow Integration

Composes:
- RuntimeRecoveryHookAdapter
- AdaptiveRetryExecutionHarness
- RecoveryOutcomeGuard
- RecoveryResultBundle

Validated scenarios:
- default-disabled blocking
- timeout recovery with chunk split
- provider_not_attempted recovery with injected rebuild callback
- too-short output rejection
- authentication error rejection

The flow remains isolated and does not modify Provider Runtime, Translation
Runtime, launcher, HTTP, or API key behavior.

## Validation

```powershell
python tools\apply_stage_415.py
python ntpe_te_v41_stage411_adaptive_retry_execution_harness_test.py
python ntpe_te_v41_stage412_runtime_recovery_hook_adapter_test.py
python ntpe_te_v41_stage413_recovery_outcome_guard_test.py
python ntpe_te_v41_stage414_recovery_result_bundle_test.py
python ntpe_te_v41_stage415_recovery_flow_integration_test.py
python -m pytest tests\integration\translation_reliability_stage411_adaptive_retry_execution_harness_test.py tests\integration\translation_reliability_stage412_runtime_recovery_hook_adapter_test.py tests\integration\translation_reliability_stage413_recovery_outcome_guard_test.py tests\integration\translation_reliability_stage414_recovery_result_bundle_test.py tests\integration\translation_reliability_stage415_recovery_flow_integration_test.py -q
python ntpe_validate.py
```
