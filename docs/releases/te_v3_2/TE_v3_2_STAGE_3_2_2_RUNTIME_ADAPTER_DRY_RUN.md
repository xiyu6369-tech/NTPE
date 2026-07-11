# TE v3.2 Stage-3.2.2 Runtime Adapter Dry Run

## Scope

This stage adds a dry-run harness for the Stage-3.2.1 Runtime Scheduler Adapter.

## Goals

- Validate runtime-adapter success flow with mock chunks.
- Validate runtime-adapter failure flow with mock handler errors.
- Produce scheduler summary, collector manifest, failed chunk report, dashboard report, and export outputs.
- Keep Provider Runtime, HTTP/client, API key, launcher flow, Prompt/Context/Naturalness Guard, and Translation Runtime untouched.

## Added Files

- `core/translation_scheduler/runtime_adapter_dry_run.py`
- `ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py`
- `tests/integration/translation_scheduler_stage322_runtime_adapter_dry_run_test.py`
- `docs/releases/TE_v3_2_STAGE_3_2_2_RUNTIME_ADAPTER_DRY_RUN.md`

## Validation

```powershell
python ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py
python -m pytest tests\integration\translation_scheduler_stage322_runtime_adapter_dry_run_test.py -q
python ntpe_validate.py
```

## Expected Output

- `NTPE TE-v3.2 Stage-3.2.2 Runtime Adapter Dry Run PASS`
- pytest: `1 passed`
- `ntpe_validate.py`: `ALL PASS`

## Risk

- The dry-run harness delegates to `RuntimeSchedulerAdapter.run_with_handler()` when available.
- If the adapter contract changes later, this harness may need a compatibility shim.
- No production runtime execution is introduced in this stage.
