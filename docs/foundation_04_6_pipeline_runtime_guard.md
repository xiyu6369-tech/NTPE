# NTPE Foundation-04.6 Pipeline Runtime Guard

Foundation-04.6 adds an additive runtime guard layer on top of the existing NTPE contracts:

- Foundation-04.3 Context Contract
- Foundation-04.4 Pipeline State Contract
- Foundation-04.5 Pipeline Execution Trace

## Files

- `core/pipeline_runtime_guard.py`
- `core/pipeline_runtime_guard_adapter.py`
- `tests/launcher_pipeline_runtime_guard_test.py`

## Purpose

The runtime guard validates pipeline objects before and after stage/plugin/adapter execution. It prevents malformed payload, state, or execution trace data from silently moving deeper into the Production Pipeline.

## Compatibility

This update is additive. It does not remove or replace existing context, state, trace, adapter, plugin, or production pipeline behavior.

## Key APIs

- `guard_payload(payload)`
- `guard_state(state)`
- `guard_trace(trace)`
- `guard_runtime(runtime)`
- `guard_before_stage(state, stage)`
- `guard_after_stage(state, stage)`
- `guard_failure(state, stage, error)`
- `guarded_call(state, stage, fn)`
- `PipelineRuntimeGuardAdapter`

## Test

```bat
cd /d D:\Python\NTPE
python tests\launcher_pipeline_runtime_guard_test.py
```

Expected final output:

```text
PASS
```
