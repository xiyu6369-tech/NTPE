# TE v3.8 Stage-3.8.2 Controlled Runtime Trial Admission Gate

## Scope

This stage adds `ControlledRuntimeTrialAdmissionGate`, a fail-closed metadata-only decision gate for a future isolated dry-run trial.

Admission requires a valid Stage-3.8.1 contract, a mock-only readiness approval, an explicitly enabled caller-supplied feature flag, the `translation_runtime` caller, the `isolated_dry_run` trial mode, and an input tree with no forbidden keys.

## Safety behavior

- Admission is rejected by default.
- Forbidden keys are detected recursively in mappings and sequences.
- Request summaries contain metadata only and retain no raw input.
- An admitted decision does not execute a scheduler, adapter, bridge, Runtime, or Provider.
- `execution_allowed` and `real_runtime_allowed` remain false.
- Immediate rollback remains available.
- Provider, HTTP, API key, launcher, and Translation Runtime access remain forbidden or untouched.

## Validation

```powershell
python ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py
python ntpe_te_v38_stage382_controlled_runtime_trial_admission_gate_test.py
python -m pytest tests\integration\translation_scheduler_stage381_controlled_runtime_trial_contract_test.py tests\integration\translation_scheduler_stage382_controlled_runtime_trial_admission_gate_test.py -q
python ntpe_validate.py
```

## Risk

`admitted_for_isolated_dry_run` is only a decision for a future stage. It does not authorize or perform execution, and all evidence remains caller-supplied metadata.

## Next stage

TE v3.8 Stage-3.8.3 Controlled Runtime Trial Rollback Controller.
