# Translation Engine Refactoring v1.8 — Character Tone + API Stability

## Changes

- Added Ilay tone guard to avoid overly light wording such as `伊萊開心地笑了`.
- Normalized ambiguous reply phrasing to preserve `어떤 쪽으로도 해석할 수 있는 짤막한 대답`.
- Added adaptive first-attempt timeout for short chunks. Short chunks now fail faster on provider hangs while preserving the configured timeout for later retries and larger chunks.
- Progress log now displays effective provider timeout per attempt.

## Verification

- `ntpe_ter_v18_character_tone_api_stability_test.py`
- `tests/integration/launcher_ter_v18_character_tone_api_stability_test.py`
- `tests/smoke/launcher_ter_v18_character_tone_api_stability_smoke_test.py`
- `ntpe_validate.py`
