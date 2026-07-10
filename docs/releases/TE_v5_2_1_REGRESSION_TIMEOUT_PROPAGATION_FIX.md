# TE v5.2.1 Regression Timeout Propagation Fix

## Scope

This incremental stage fixes propagation of `launcher_translate.py regression --api-timeout` without enabling or changing the TE v5.0-v5.2 Quality Runtime Pipeline.

## Root cause

An explicit timeout such as 180 seconds was written to `NTPE_API_TIMEOUT`, but two runtime clamps reduced it to the active speed-policy timeout (typically 120 seconds):

1. `core/translation_runtime/runtime_speed_policy.py::effective_timeout`
2. `lts/txt_translation_runtime.py::_effective_provider_timeout`

## Corrected behavior

- Explicit CLI timeout: authoritative end-to-end.
- No explicit CLI timeout: existing speed-profile timeout behavior is unchanged.
- Existing short-chunk first/retry timeout defaults remain unchanged.
- Provider transport continues to receive the calculated value through `NTPE_CURRENT_API_TIMEOUT`.

## Validation

```bat
python ntpe_te_v521_timeout_propagation_fix_test.py
python ntpe_te_v30_stage022_runtime_speed_policy_test.py
python ntpe_validate.py
```

Golden Set:

```bat
python launcher_translate.py regression ^
--set golden ^
--stage TE-v5.2.1-TimeoutPropagation ^
--profile literary ^
--chunk-size 600 ^
--api-timeout 180 ^
--overwrite
```

Expected provider progress/debug output must show `timeout=180s`, not `120s`.
