# NTPE 1.2 Translation Engine Refactoring v2.0

## Quality Lock Baseline

TER-v2.0 establishes a hard quality floor for the production translator before further style polishing.

### Added

- Quality Lock Baseline for known Smoke_Set semantic regressions.
- QA detection for invalid reply-object structures such as `留下了鄭泰義一個回答`.
- QA detection for near-duplicate disappearance descriptions.
- QA detection for unstable fatigue phrasing.
- Short-chunk provider timeout fast-fail behavior.
- Correct per-attempt timeout handling via `NTPE_CURRENT_API_TIMEOUT`.

### Fixed

- Provider logs could show adaptive timeout while requests still waited the global timeout.
- Short Smoke_Set requests could burn multiple 180-second waits before failure.
- Recurrent output defects around Ilay's ambiguous answer and Tae-ui's wall-slide scene.

### Validation

- `ntpe_ter_v20_quality_lock_baseline_test.py`
- `tests/integration/launcher_ter_v20_quality_lock_baseline_test.py`
- `tests/smoke/launcher_ter_v20_quality_lock_baseline_smoke_test.py`
- `ntpe_validate.py`
