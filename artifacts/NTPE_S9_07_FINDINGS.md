# NTPE S9-07 — Findings

**Date**: 2026-10-02
**Scope**: S9-07 Reader-First E2E Acceptance

---

## Finding F1 — EPUB translation entry capability gap (PRE-EXISTING / DEFERRED)

**Classification**: B/C — pre-existing defect / missing product capability (NOT an S9-07 regression).

**Evidence**:
- The production EPUB entry (`ProjectPage._on_translate` → `_build_epub_options`) routes correctly to the canonical EPUB path.
- `_build_epub_options` calls canonical chunking (`chunk_epub_translation_input`), which requires
  `EpubChapterBoundary.body_start_offset` / `body_end_offset`.
- `core/adapters/epub_extraction_boundary.py` constructs `EpubChapterBoundary` with only
  `start_offset` / `end_offset` (lines ~214-215); body offsets remain `None`.
- Result: `ValueError: Chapter <id> missing body offsets; cannot perform chapter-aware chunking`.
- All prior EPUB launch tests (`test_epub_translation_launch.py`, `test_s8_03_output_policy.py::test_d`)
  **mock `_build_epub_options`**, so the real options-building path was never exercised.

**Impact**: EPUB cannot currently enter real translation through the Production UI. TXT is unaffected.

**Scope decision**: This is not an S9-07 regression and not caused by S9 phase work. Fixing it would
require changing the frozen EPUB extraction/chunking boundary (out of S9-07 scope). Per S9-07 §22/§41
and §26 (frozen runtime), no fake route was added and no frozen boundary was modified.

**S9-07 disposition**: EPUB Translation Entry / Translation / Packaging / Output = **DEFERRED**.
EPUB Import / Extraction / Preview / Project Persistence / Isolation = PASS.

**Minimal required follow-up (future, not S9-07)**:
populate chapter body offsets in `EpubExtractionBoundary` (or relax canonical chunking to derive body
ranges from `start_offset`/`end_offset`), then re-run EPUB E2E. This is an EPUB-layer contract change,
tracked outside S9.

---

## Pre-existing issues (unchanged)

| Issue | Status |
|-------|--------|
| `tests/ui/test_translation_studio_shell.py` `window.close()` hang | PRE-EXISTING / OUT-OF-SCOPE |
| `tests/literary/outputs/PS-03/README.md` deleted | PRE-EXISTING / UNTOUCHED |
| 3 literary residual files modified | PRE-EXISTING / UNTOUCHED |

---

## Stop conditions

No S9-07 stop condition triggered. The EPUB gap is classified and deferred, not worked around.
