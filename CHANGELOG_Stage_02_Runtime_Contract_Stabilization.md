# NTPE 1.2 Professional — Stage-02 Runtime Contract Stabilization

Status: ALL PASS ✅

## Summary

Stage-02 formalizes the NTPE 1.2 Translation Runtime public contract without modifying Foundation v1.0 or breaking NTPE 1.1 LTS compatibility.

## Added

- `core/translation_runtime/runtime_contract.py`
- Runtime contract dataclasses and validation helpers
- Runtime diagnostic APIs:
  - `TranslationRuntime.describe()`
  - `TranslationRuntime.validate_compatibility()`
- Stage-02 regression tests for runtime contract stability

## Changed

- `TranslationRuntime.version` updated to `1.2-professional-stage-02`
- `core.translation_runtime` exports runtime contract helpers
- Existing Stage-01 runtime tests updated to the Stage-02 version string

## Compatibility

- `launcher_translate.py`: compatible
- `ntpe_translate_txt.py`: compatible
- `ntpe_translate_batch.py`: compatible
- NTPE 1.1 LTS TXT / Batch runtime: callable through official runtime facade
- Foundation v1.0: untouched

## Tests

```text
python -m pytest tests/runtime/translation_runtime_test.py tests/smoke/runtime_smoke_test.py tests/runtime/translation_runtime_contract_test.py -q
7 passed

python -m compileall -q core lts tests/runtime tests/smoke
ALL PASS
```
