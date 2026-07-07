# Translation Engine Refactoring v1.9 — Stability + Repetition Guard

## Focus
- Reduce wasted retry time when NVIDIA workers return 503/ResourceExhausted or hang.
- Add configurable provider fallback model chain without changing the default primary model.
- Stabilize Smoke_Set phrasing around Ilay's ambiguous answer, disappearance repetition, and fatigue narration.

## Changes
- Added `NTPE_FALLBACK_MODELS` support. Example: `set NTPE_FALLBACK_MODELS=model_a,model_b`.
- Progress output now includes provider model and active timeout per attempt.
- Retry timeout can be capped with `NTPE_RETRY_TIMEOUT`.
- Capacity retry delay can be capped with `NTPE_CAPACITY_RETRY_MAX_WAIT`.
- Strengthened repetition guard for repeated `消失在視線` patterns.
- Strengthened fatigue normalization for `幾十年的疲勞...湧上來` variants.

## Validation
- `python ntpe_ter_v19_stability_repetition_guard_test.py`
- `python tests\integration\launcher_ter_v19_stability_repetition_guard_test.py`
- `python tests\smoke\launcher_ter_v19_stability_repetition_guard_smoke_test.py`
- `python ntpe_validate.py`
