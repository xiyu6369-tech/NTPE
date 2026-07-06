# NTPE 1.2 Professional — Stage-15.1 Translation Quality Engine Core

Stage-15.1 introduces the first formal Translation Quality Engine Core layer.

## Added

- `core.quality.TranslationQualityEngine`
- `QualityContext`, `QualityResult`, `QualityIssue`
- Rule registry and deterministic quality pipeline
- Default core rules:
  - Non-empty translation
  - Source/target length ratio
  - Placeholder integrity
- Quality event bus
- Quality report JSON/text helpers
- Unit and integration tests
- Launcher: `ntpe_stage15_1_quality_engine_core_test.py`

## Compatibility

This stage is additive only. It does not modify Foundation v1.0, NTPE 1.1 LTS Frozen,
or the Stage-14 Provider Framework Freeze public contracts.
