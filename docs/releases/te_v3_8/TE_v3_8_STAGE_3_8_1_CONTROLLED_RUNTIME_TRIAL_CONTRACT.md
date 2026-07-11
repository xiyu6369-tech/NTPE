# TE v3.8 Stage-3.8.1 Controlled Runtime Trial Contract

## Scope

This stage introduces `ControlledRuntimeTrialContract`, a contract-only definition for a future controlled Runtime integration trial.

The contract is disabled by default, requires explicit opt-in, supports immediate rollback, and prohibits Runtime execution, real translation, Provider access, HTTP access, API key access, launcher changes, and Translation Runtime flow changes.

## Files

- `core/translation_scheduler/controlled_runtime_trial_contract.py`
- `ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py`
- `tests/integration/translation_scheduler_stage381_controlled_runtime_trial_contract_test.py`
- `manifests/te_v38_controlled_runtime_trial_contract_manifest.json`

## Guarantees

- Contract construction and validation only.
- TE v3.2 through TE v3.7 Freeze guarantees remain unchanged.
- No scheduler or adapter is instantiated and no job is enqueued.
- No bridge, Provider, HTTP client, API key, launcher, or Translation Runtime path is called.
- `source_text`, `text`, and `chunks` are forbidden trial inputs.
- Execution and real Runtime access remain disallowed.

## Validation

```powershell
python ntpe_te_v38_stage381_controlled_runtime_trial_contract_test.py
python -m pytest tests\integration\translation_scheduler_stage381_controlled_runtime_trial_contract_test.py -q
python ntpe_validate.py
```

## Risk

This contract does not admit or execute a trial request. A later admission gate must preserve the same disabled-by-default and immediate-rollback boundaries.

## Next stage

TE v3.8 Stage-3.8.2 Controlled Runtime Trial Admission Gate.
