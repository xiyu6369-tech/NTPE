# Translation Engine Refactoring v1.6 — Semantic Guard

## Purpose

TER-v1.6 fixes polish-side semantic regressions found during Smoke_Set testing.
It does not add outer-platform features.  It keeps the TER-v1.4/v1.5 prompt
compression and name-lock behavior while preventing literary cleanup from
changing sentence meaning.

## Changes

- Added semantic guards to `core/literary/literary_style_normalizer.py`.
- Repairs awkward ambiguous-answer structures such as:
  - `留下了鄭泰義一個簡短的回答`
  - normalized to an Ilay-centered short answer expression.
- Deduplicates repeated disappearance descriptions, especially:
  - `直到伊萊...消失...` followed by `等伊萊徹底消失...`
- Retains existing v1.5 polish improvements:
  - `抬了抬眉毛` → `挑了挑眉`
  - `事情已經變得最壞了` → `事情已經糟到不能再糟`

## Validation

```bat
python ntpe_ter_v16_semantic_guard_test.py
python tests\integration\launcher_ter_v16_semantic_guard_test.py
python tests\smoke\launcher_ter_v16_semantic_guard_smoke_test.py
python ntpe_validate.py
```
