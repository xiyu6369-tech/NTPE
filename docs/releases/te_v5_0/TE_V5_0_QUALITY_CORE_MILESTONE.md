# TE v5.0 Translation Quality Core Milestone

## Scope

This milestone adds a standalone Korean→Traditional Chinese quality core:

1. Stage-5.0.1 Translation Quality Baseline
2. Stage-5.0.2 Completeness Guard
3. Stage-5.0.3 Terminology Consistency Guard
4. Stage-5.0.4 Traditional Chinese Normalizer
5. Stage-5.0.5 Quality Core Pipeline
6. Stage-5.0.6 Quality Core Freeze

## Behavior

The pipeline detects:
- empty or abnormally short output
- likely omissions or summarization
- Hangul residue
- duplicate paragraphs and lines
- locked terminology mismatches
- dialogue quote format issues
- common simplified-Chinese residue

It returns explicit repair and retry actions. It does not execute translation,
call a provider, access HTTP or API keys, or modify Translation Runtime.

## Commands

```powershell
python tools\apply_te_v50_quality_core.py
python ntpe_te_v50_quality_core_milestone_test.py
python ntpe_te_v50_stage506_quality_core_freeze_test.py
python -m pytest tests\integration\translation_quality_v50_quality_core_milestone_test.py tests\integration\translation_quality_v50_stage506_freeze_test.py -q
python ntpe_validate.py
```
