# NTPE 1.2 Production Stabilization — PS-04

## Added

- `core/literary/` narrative-aware prompt modules.
- Literary translation policy separated from runtime code.
- Narrative context analysis for scene, mood, lexical and long sentence hints.
- Character context analysis for locked characters and subject hints.
- Glossary context with immutable term rendering and alias corrections.
- Integration into `lts/txt_translation_runtime.py` prompt package generation.

## Compatibility

- Does not modify Foundation v1.0 or NTPE 1.1 LTS frozen behavior.
- Keeps existing `launcher_translate.py batch/txt/regression/evaluate` commands.
- `novel` remains accepted as alias for `literary`.
