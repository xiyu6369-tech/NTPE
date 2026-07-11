# TE v4.0 Stage-4.0.2 Adaptive Retry Policy

Adds a pure retry decision engine.

The policy maps reliability outcomes to:
- retry or stop
- backoff delay
- next timeout
- next chunk size
- provider session rebuild suggestion
- provider switch suggestion

No retry is actually executed in this stage.

## Main behavior

- HTTP 429 / 503: exponential backoff
- read timeout: increase timeout and halve chunk size
- provider_attempted=0: request provider session rebuild
- empty / too short / Hangul residue: immediate retry with smaller chunk
- authentication / forbidden / invalid request: stop
- max attempts reached: stop

## Validation

```powershell
python apply_stage_402.py
python ntpe_te_v40_stage402_adaptive_retry_policy_test.py
python -m pytest tests\integration\translation_reliability_stage402_adaptive_retry_policy_test.py -q
python ntpe_validate.py
```
