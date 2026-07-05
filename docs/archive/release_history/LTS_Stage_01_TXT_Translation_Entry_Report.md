# NTPE 1.1 LTS Stage-01 — TXT Translation Entry Report

## Scope
This stage adds the first formal TXT novel translation entry for NTPE 1.1 LTS.

## Added Files
- `ntpe_translate_txt.py`
- `lts/txt_translation_runtime.py`
- `README_NTPE_1_1_LTS_Stage_01.txt`
- `CHANGELOG_NTPE_1_1_LTS_Stage_01.md`
- `tests/lts_stage_01/test_txt_translation_runtime.py`
- `tests/lts_stage_01/launcher_txt_translation_entry_test.py`

## Compatibility
- NTPE 1.0 Stable remains intact.
- Existing TranslationEngine is reused as backend.
- No frozen module behavior is changed.

## User Command
```bat
python ntpe_translate_txt.py input\novel.txt output
```

## Dry Run Command
```bat
python ntpe_translate_txt.py input\novel.txt output --dry-run
```
