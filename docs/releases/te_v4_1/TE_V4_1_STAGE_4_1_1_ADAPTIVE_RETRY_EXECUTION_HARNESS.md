# TE v4.1 Stage-4.1.1 Adaptive Retry Execution Harness

This stage turns the existing retry policy and split planner into an isolated,
callback-driven execution harness.

It can:
- retry injected handlers
- apply adaptive timeout changes
- split failed chunks
- call an injected provider-session rebuild callback
- stop on non-retryable failures

It does not import or modify Provider Runtime, Translation Runtime, launcher,
HTTP clients, or API keys.

## Validation

```powershell
python tools\apply_stage_411.py
python ntpe_te_v41_stage411_adaptive_retry_execution_harness_test.py
python -m pytest tests\integration\translation_reliability_stage411_adaptive_retry_execution_harness_test.py -q
python ntpe_validate.py
```
