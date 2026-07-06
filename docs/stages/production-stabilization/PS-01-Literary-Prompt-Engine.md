# PS-01 Literary Prompt Engine

Production Stabilization starts here. The goal is literary translation quality, not additional enterprise features.

## Core policy

NTPE translates Korean novels into natural literary Traditional Chinese that fits the work's era, setting, culture, and narrative voice. It must not force a specific regional vocabulary when the story context suggests another natural expression.

## Added

- Literary prompt policy.
- `literary`, `balanced`, and `premium` profiles while keeping `novel` and `quality` backward compatible.
- Literary regression corpus structure under `tests/literary`.
- Prompt package metadata: `1.2-ps-01-literary-prompt-engine`.

## Validation

```bat
python ntpe_ps01_literary_prompt_engine_test.py
python tests\integration\launcher_ps01_literary_prompt_engine_test.py
python tests\smoke\launcher_ps01_literary_prompt_engine_smoke_test.py
python ntpe_validate.py
```
