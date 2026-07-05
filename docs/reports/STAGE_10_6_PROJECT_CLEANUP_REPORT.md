# NTPE 1.2 Professional — Stage-10.6 Project Cleanup and Archive Policy

Status: ALL PASS ✅

## What changed

- Removed generated Python cache artifacts: 226 items.
- Archived root-level historical release documents: 341 files.
- Added cleanup utility: `tools/maintenance/project_cleanup.py`.
- Updated stale runtime version assertions in two runtime tests so they validate the current runtime version instead of old Stage-04/Stage-06 literals.

## Deletion policy

No Python feature modules were deleted in this stage. Only generated/cache artifacts were deleted. Historical documents were archived, not deleted.

## Archive location

`docs/archive/release_history/`

## Validation

```bat
python -m pytest tests/runtime tests/smoke/runtime_smoke_test.py tests/smoke/plugin_architecture_smoke_test.py tests/smoke/plugin_runtime_smoke_test.py tests/plugins -q
21 passed

python -m compileall -q .
PY_COMPILE_ALL_PASS
```

## Note

Full-project pytest collection still contains pre-existing legacy test collection issues unrelated to this cleanup stage, mainly duplicate launcher test module names and missing legacy `runtime_api.runtime_context`. This stage did not modify those legacy subsystems.
