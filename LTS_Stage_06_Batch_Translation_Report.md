# NTPE 1.1 LTS Stage-06 Batch Folder Translation Report

Status: ALL PASS

## Scope
- Added batch folder translation entry.
- Added natural sort scanner.
- Added recursive folder option.
- Added skip-completed behavior.
- Added batch JSON/Markdown report generation.
- Reuses Stage-01~05 TXT runtime for resume, retry, glossary, character memory, QA, and output formatter.

## Compatibility
- Foundation v1.0 Frozen preserved.
- CLI Frozen preserved.
- SDK Frozen preserved.
- Runtime API Frozen preserved.
- Web UI Frozen preserved.
- Existing ntpe_translate_txt.py remains compatible.

## Tests
- Stage-06 tests: PASS
- LTS Stage-01~05 regression: PASS
- Stable regression: PASS
- Clean Project Tool: PASS
- Total: 46 passed
