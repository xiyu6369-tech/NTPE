# NTPE 1.2 Translation Engine Refactoring v1.3

## Focus
Speed + Prompt Compression.

## Changes
- Compress Literary Prompt v4 to reduce repeated policy/context text.
- Compact Dynamic Glossary rendering.
- Compact Character/Narrative context rendering.
- Reduce default `max_output_tokens` per profile:
  - fast: 500-1200
  - balanced: 600-1600
  - literary/novel: 700-2200
  - premium/quality: 900-3000
- Add `max_tokens` to progress/debug visibility.
- Add conservative style cleanup for common Smoke Set output issues.

## Validation
- `python ntpe_ter_v13_speed_prompt_compression_test.py`
- `python tests/integration/launcher_ter_v13_speed_prompt_compression_test.py`
- `python tests/smoke/launcher_ter_v13_speed_prompt_compression_smoke_test.py`
- `python ntpe_validate.py`

All pass.
