# TE v3.7 Stage-3.7.4 Runtime Readiness Decision

## Summary

Stage-3.7.4 combines the readiness contract, metadata-only evidence collector, and evaluator into one non-executing decision. Approval permits only the next mock-only planning step.

## Added Files

- `core/translation_scheduler/runtime_readiness_decision.py`
- `ntpe_te_v37_stage374_runtime_readiness_decision_test.py`
- `tests/integration/translation_scheduler_stage374_runtime_readiness_decision_test.py`
- `docs/releases/te_v3_7/TE_v3_7_STAGE_3_7_4_RUNTIME_READINESS_DECISION.md`

## Modified Files

- `core/translation_scheduler/__init__.py`

## Guarantees

- Accepts only caller-supplied mappings and performs no external discovery.
- Missing, incomplete, or unsafe evidence is rejected.
- Approval is named `approved_for_mock_only` and never authorizes execution.
- `next_allowed_mode` is always `mock_only`.
- `real_runtime_allowed` and `execution_allowed` are always `false`.
- Raw `source_text`, `text`, and `chunks` fields are not retained.
- No bridge, scheduler, Provider Runtime, HTTP/client, API key, launcher, Translation Runtime, or real translation path is used.

## Validation

```powershell
python ntpe_te_v32_runtime_scheduler_freeze_test.py
python ntpe_te_v33_runtime_integration_freeze_test.py
python ntpe_te_v34_runtime_optin_hook_freeze_test.py
python ntpe_te_v35_runtime_disabled_trial_freeze_test.py
python ntpe_te_v36_runtime_safe_hook_preflight_freeze_test.py
python ntpe_te_v37_stage371_runtime_readiness_gate_contract_test.py
python ntpe_te_v37_stage372_runtime_readiness_gate_evaluator_test.py
python ntpe_te_v37_stage373_runtime_readiness_evidence_collector_test.py
python ntpe_te_v37_stage374_runtime_readiness_decision_test.py
python -m pytest tests\integration\translation_scheduler_v32_runtime_scheduler_freeze_test.py tests\integration\translation_scheduler_v33_runtime_integration_freeze_test.py tests\integration\translation_scheduler_v34_runtime_optin_hook_freeze_test.py tests\integration\translation_scheduler_v35_runtime_disabled_trial_freeze_test.py tests\integration\translation_scheduler_v36_runtime_safe_hook_preflight_freeze_test.py tests\integration\translation_scheduler_stage371_runtime_readiness_gate_contract_test.py tests\integration\translation_scheduler_stage372_runtime_readiness_gate_evaluator_test.py tests\integration\translation_scheduler_stage373_runtime_readiness_evidence_collector_test.py tests\integration\translation_scheduler_stage374_runtime_readiness_decision_test.py -q
python ntpe_validate.py
```

## Risk

- The decision trusts normalized caller-supplied metadata; it does not attest external state.
- Approval does not enable or execute a real runtime integration.

## Next Stage

`TE v3.7 Stage-3.7.5 Runtime Readiness Freeze`
