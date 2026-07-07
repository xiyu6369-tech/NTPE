# NTPE 1.2 Translation Engine Refactoring v1.2

## Focus
Literary Style Engine for the core translator. This release avoids new external features and improves the actual Chinese novel output.

## Changes
- Added `core/literary/literary_style_normalizer.py`.
- Added conservative Chinese-novel style cleanup for common MT phrasing.
- Expanded simplified-to-traditional normalization for high-frequency provider output such as `扬`.
- Updated compact literary prompt policy to emphasize Chinese novel prose, idiom handling, and action phrasing.
- Updated prompt mode to `compact_literary_v3_ter_v1_2`.
- Integrated literary style normalization into final TXT output formatting.
- Added TER-v1.2 root, integration, and smoke tests.

## Validation
- `python ntpe_ter_v12_literary_style_engine_test.py`
- `python tests\integration\launcher_ter_v12_literary_style_engine_test.py`
- `python tests\smoke\launcher_ter_v12_literary_style_engine_smoke_test.py`
- `python ntpe_validate.py`

All pass.
