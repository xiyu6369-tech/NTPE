# NTPE 1.2 Professional — Stage-01 Translation Runtime Integration

## Status

ALL PASS

## Scope

Stage-01 introduces the official `core.translation_runtime` facade and routes all public translation entries through it:

- `launcher_translate.py`
- `ntpe_translate_txt.py`
- `ntpe_translate_batch.py`

## Compatibility

- Foundation v1.0 untouched.
- NTPE 1.1 LTS modules preserved.
- `launcher_translate.py` compatibility preserved.
- LTS TXT and batch APIs remain importable.
- Existing CLI arguments are preserved through the LTS parsers.

## Runtime Pipeline

Encoding → Chunk → Context → Glossary → Character Memory → Prompt Builder → AI Provider → QA → Taiwan Formatter → Output

## Added

- `core/translation_runtime/__init__.py`
- `core/translation_runtime/runtime.py`
- `core/translation_runtime/runtime_encoding.py`
- `core/translation_runtime/runtime_chunk.py`
- `core/translation_runtime/runtime_context.py`
- `core/translation_runtime/runtime_formatter.py`
- `core/translation_runtime/runtime_output.py`
- `tests/runtime/translation_runtime_test.py`
- `tests/smoke/runtime_smoke_test.py`

## Changed

- `launcher_translate.py` now uses `TranslationRuntime`.
- `ntpe_translate_txt.py` now uses `core.translation_runtime.main_txt`.
- `ntpe_translate_batch.py` now uses `core.translation_runtime.main_batch`.
