# TE v4.2 Stage-4.2.3 Real Runtime Recovery Pilot Rollback Controller

## Summary

Stage 4.2.3 adds `RealRuntimeRecoveryPilotRollbackController`, an
idempotent rollback controller for the real-runtime recovery pilot.

The controller only derives a safe rollback result from caller-supplied
metadata. It does not call admission gates, recovery flows, retry harnesses,
providers, HTTP clients, API keys, Translation Runtime, Provider Runtime, or
launcher code.

## Files

Modified:

- `core/translation_reliability/__init__.py`

Added:

- `core/translation_reliability/real_runtime_recovery_pilot_rollback_controller.py`
- `ntpe_te_v42_stage423_real_runtime_recovery_pilot_rollback_controller_test.py`
- `tests/integration/translation_reliability_stage423_real_runtime_recovery_pilot_rollback_controller_test.py`
- `manifests/te_v42_real_runtime_recovery_pilot_rollback_manifest.json`
- `docs/releases/te_v4_2/TE_V4_2_STAGE_4_2_3_REAL_RUNTIME_RECOVERY_PILOT_ROLLBACK_CONTROLLER.md`

## Safety Guarantees

- Rollback is always available.
- Rollback is idempotent.
- Result mode is always `disabled`.
- Admission status is always revoked.
- Execution remains disabled.
- Real provider request remains disabled.
- Real translation remains disabled.
- Provider Runtime touch mode remains `none`.
- Translation Runtime touch mode remains `none`.
- Launcher touch mode remains `none`.
- Raw source text, translated text, chunks, API keys, and provider clients are
  not retained.

## Supported Previous States

- missing state
- disabled
- admitted_for_single_chunk_dry_run
- single_chunk_dry_run
- dry_run_running
- dry_run_completed
- recovery_completed
- recovery_rejected
- error
- unknown

## Validation

```powershell
python ntpe_te_v40_stage408_translation_reliability_freeze_test.py
python ntpe_te_v41_stage417_translation_reliability_execution_freeze_test.py
python ntpe_te_v42_stage421_real_runtime_recovery_pilot_contract_test.py
python ntpe_te_v42_stage422_real_runtime_recovery_pilot_admission_gate_test.py
python ntpe_te_v42_stage423_real_runtime_recovery_pilot_rollback_controller_test.py
python -m pytest tests\integration\translation_reliability_stage408_freeze_test.py tests\integration\translation_reliability_stage417_execution_freeze_test.py tests\integration\translation_reliability_stage421_real_runtime_recovery_pilot_contract_test.py tests\integration\translation_reliability_stage422_real_runtime_recovery_pilot_admission_gate_test.py tests\integration\translation_reliability_stage423_real_runtime_recovery_pilot_rollback_controller_test.py -q
python ntpe_validate.py
```

## Next Stage

TE v4.2 Stage-4.2.4 Single-Chunk Dry-Run Runner.
