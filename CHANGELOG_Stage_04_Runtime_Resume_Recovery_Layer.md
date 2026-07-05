# NTPE 1.2 Professional — Stage-04 Runtime Resume / Recovery Layer

## Status

ALL PASS

## Scope

Stage-04 adds an additive Runtime Recovery Layer on top of the Stage-03 Runtime Provider / QA Boundary.

## Added

- `core/translation_runtime/runtime_recovery.py`
- Runtime facade checkpoint APIs:
  - `checkpoint(scope, name, **cursor)`
  - `checkpoint_error(scope, name, error, **cursor)`
  - `checkpoint_completed(scope, name, **metadata)`
  - `recovery_summary()`
- Runtime contract capability:
  - `runtime_recovery`
- Runtime recovery tests:
  - `tests/runtime/translation_runtime_recovery_test.py`

## Compatibility

- Foundation v1.0 untouched.
- NTPE 1.1 LTS resume files untouched.
- `launcher_translate.py`, `ntpe_translate_txt.py`, and `ntpe_translate_batch.py` remain compatible.
- Stage-04 only adds runtime-level checkpoints under `.ntpe_runtime_checkpoints/`.

## Pipeline

Encoding → Chunk → Context → Glossary → Character Memory → Prompt Builder → AI Provider → QA → Taiwan Formatter → Output → Recovery
