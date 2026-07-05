# NTPE 1.1 LTS Stage-01 — TXT Translation Entry

## Added
- `ntpe_translate_txt.py` command entry.
- `lts/txt_translation_runtime.py` TXT runtime adapter.
- TXT encoding auto-detection.
- Paragraph-aware chunk splitting.
- Prompt Package generation for each TXT chunk.
- Chunk resume and final output merge.
- Stage-01 tests and launcher validation.

## Compatibility
- No existing NTPE 1.0 Stable module was overwritten.
- Uses existing `TranslationEngine` as the execution backend.
