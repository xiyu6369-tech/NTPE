# TE v4.2 Stage-4.2.1 Real Runtime Recovery Pilot Contract

This stage defines the contract for a future, opt-in, single-chunk recovery
pilot from Translation Runtime into the TE v4.1 recovery flow.

## Scope

- Contract only
- Disabled by default
- Explicit opt-in only
- Single chunk only
- Immediate rollback required
- No Provider Runtime changes
- No Translation Runtime changes
- No launcher changes
- No HTTP or API key access
- No real provider request
- No real translation execution
- No source or translated text retention

## Added

- `core/translation_reliability/real_runtime_recovery_pilot_contract.py`
- `ntpe_te_v42_stage421_real_runtime_recovery_pilot_contract_test.py`
- `tests/integration/translation_reliability_stage421_real_runtime_recovery_pilot_contract_test.py`
- `manifests/te_v42_real_runtime_recovery_pilot_contract_manifest.json`

## Validation

```powershell
python ntpe_te_v40_stage408_translation_reliability_freeze_test.py
python ntpe_te_v41_stage417_translation_reliability_execution_freeze_test.py
python ntpe_te_v42_stage421_real_runtime_recovery_pilot_contract_test.py

python -m pytest tests\integration\translation_reliability_stage408_freeze_test.py tests\integration\translation_reliability_stage417_execution_freeze_test.py tests\integration\translation_reliability_stage421_real_runtime_recovery_pilot_contract_test.py -q

python ntpe_validate.py
```

## Next

`TE v4.2 Stage-4.2.2 Real Runtime Recovery Pilot Admission Gate`
