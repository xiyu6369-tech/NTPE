# TE v3.6 Stage-3.6.4 Runtime Safe Hook Preflight Boundary Regression

## Summary

Stage-3.6.4 adds boundary regression coverage for the Runtime Safe Hook Preflight layer.
It verifies that the Stage-3.6.1 contract, Stage-3.6.2 guard, and Stage-3.6.3 mock bridge remain disabled-by-default and mock-only.

## Added Files

- `ntpe_te_v36_stage364_runtime_safe_hook_preflight_boundary_regression_test.py`
- `tests/integration/translation_scheduler_stage364_runtime_safe_hook_preflight_boundary_regression_test.py`
- `manifests/te_v36_runtime_safe_hook_preflight_boundary_manifest.json`
- `docs/releases/te_v3_6/TE_v3_6_STAGE_3_6_4_RUNTIME_SAFE_HOOK_PREFLIGHT_BOUNDARY_REGRESSION.md`

## Guarantees

- Runtime safe hook preflight remains disabled-by-default.
- Explicit opt-in remains mock-only.
- `preflight_blocked` does not call the disabled trial bridge.
- `preflight_mock_completed` does not execute real translation.
- `integration_status.executed` remains `False`.
- `integration_status.real_translation` remains `False`.
- Provider runtime remains forbidden, not connected, or external.
- HTTP/client remains forbidden or not called.
- API key remains forbidden or not used.
- `launcher_translate.py` remains unchanged.
- Translation Runtime flow remains unchanged.
- Request summaries do not store raw `source_text`, `text`, or `chunks`.
- Export outputs do not contain real translation output.

## Validation

```powershell
python ntpe_te_v32_runtime_scheduler_freeze_test.py
python ntpe_te_v33_runtime_integration_freeze_test.py
python ntpe_te_v34_runtime_optin_hook_freeze_test.py
python ntpe_te_v35_runtime_disabled_trial_freeze_test.py
python ntpe_te_v36_stage361_runtime_safe_hook_preflight_contract_test.py
python ntpe_te_v36_stage362_runtime_safe_hook_preflight_guard_test.py
python ntpe_te_v36_stage363_runtime_safe_hook_preflight_mock_bridge_test.py
python ntpe_te_v36_stage364_runtime_safe_hook_preflight_boundary_regression_test.py
python -m pytest tests\integration\translation_scheduler_v32_runtime_scheduler_freeze_test.py tests\integration\translation_scheduler_v33_runtime_integration_freeze_test.py tests\integration\translation_scheduler_v34_runtime_optin_hook_freeze_test.py tests\integration\translation_scheduler_v35_runtime_disabled_trial_freeze_test.py tests\integration\translation_scheduler_stage361_runtime_safe_hook_preflight_contract_test.py tests\integration\translation_scheduler_stage362_runtime_safe_hook_preflight_guard_test.py tests\integration\translation_scheduler_stage363_runtime_safe_hook_preflight_mock_bridge_test.py tests\integration\translation_scheduler_stage364_runtime_safe_hook_preflight_boundary_regression_test.py -q
python ntpe_validate.py
```

## Risk

- This stage is regression-only and adds no new runtime behavior.
- The preflight mock bridge remains mock-only and does not connect to Translation Runtime.
- The next recommended stage is `TE v3.6 Stage-3.6.5 Runtime Safe Hook Preflight Freeze`.
