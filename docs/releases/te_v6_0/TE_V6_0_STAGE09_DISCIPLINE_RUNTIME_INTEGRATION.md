# TE v6.0 Stage 09 - Discipline Runtime Integration

Stage 09 establishes `core.translation_discipline.runtime_integration` as the
single post-provider Translation Discipline runtime entrypoint. It coordinates
the frozen quality callbacks, Discipline Quality Enforcement, deterministic
local repair, post-repair revalidation, adaptive retry decision, adaptive
feedback metadata, and the audit trail in one `DisciplineRuntimeContext`.

`lts/txt_translation_runtime.py` remains responsible for provider execution,
resume state, output files, and acting on `DisciplineRuntimeResult`. It no
longer directly invokes the Stage 04, Stage 05, or Stage 06 coordination APIs.

All Stage 01-08 public APIs remain exported. Stage 06 is retained as the
compatibility implementation used inside the Stage 09 integration boundary.
The integration adds no provider call, HTTP client, timeout, retry delay, RPM,
prompt text, token-profile, quality-score, or Unified decision changes.

The additive metadata key is `discipline_runtime_integration`, version
`6.0.0-stage09`. Existing prompt, audit, feedback, smart-local-repair, and
best-attempt metadata remains intact.

Validation:

- `python ntpe_te_v600_stage09_discipline_runtime_integration_test.py`
- `python -m pytest -q tests/integration/translation_discipline_runtime_integration_v600_stage09_test.py`
- Stage 01-08.1 root and integration regressions
- `python ntpe_validate.py`
