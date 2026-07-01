# NTPE Foundation-04.7 Pipeline Error Recovery Contract

## Purpose
Foundation-04.7 adds a stable recovery contract on top of Foundation-04.6 Runtime Guard.
It converts runtime/stage/plugin/adapter failures into deterministic recovery decisions.

## New files

- `core/pipeline_error_recovery_contract.py`
- `core/pipeline_error_recovery_adapter.py`
- `tests/launcher_pipeline_error_recovery_test.py`

## Recovery actions

- `retry`
- `fallback`
- `skip`
- `abort`
- `escalate`
- `none`

## Compatibility

This update is additive. It does not replace:

- Foundation-04.3 Context Contract
- Foundation-04.4 Pipeline State Contract
- Foundation-04.5 Execution Trace
- Foundation-04.6 Runtime Guard

Unknown/custom fields are preserved whenever recovery records and states are normalized.

## Test

```bat
cd /d D:\Python\NTPE
python tests\launcher_pipeline_error_recovery_test.py
```

Expected result:

```text
PASS
```
