# NTPE 1.1 LTS Stage-06 - Batch Folder Translation

## Added
- Added `ntpe_translate_batch.py` batch folder translation entry.
- Added `lts/batch_translation_runtime.py`.
- Added natural TXT file sorting and optional recursive folder scan.
- Added skip-completed behavior for existing non-empty `*_zh.txt` files.
- Added batch JSON and Markdown summary reports.
- Added Stage-06 unit and launcher tests.

## Compatibility
- Preserves NTPE 1.0 Stable frozen layers.
- Preserves Stage-01 to Stage-05 TXT translation entry compatibility.
- Uses incremental extension only.
