# NTPE S10 Commit Boundary

Baseline: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e` (tag `s9-complete`)
Scope: `git diff 4a539b8` (tracked changes) plus untracked files.

Every current worktree change is classified below.
No `git add .` is permitted for the S10 commit.

Counts: INCLUDE = 21, EXCLUDE = 5, UNCERTAIN = 0.

---

## INCLUDE — S10-owned (21)

### Production (7)

| # | Path | Action | Phase | Reason |
|---|---|---|---|---|
| 1 | `core/adapters/epub_extraction_boundary.py` | M | S10-02 | F1: populate chapter body offsets |
| 2 | `core/adapters/canonical_book_intake_adapter.py` | M | S10-02 | F1: canonical extraction→intake metadata mapping |
| 3 | `core/epub_translation/output_layout.py` | A | S10-03 (F2) | pure filesystem-safe output-dir helper |
| 4 | `core/epub_translation/runtime/adapter.py` | M | S10-03 (F2) | use safe output-dir helper |
| 5 | `ui/translation_studio/translation_worker.py` | M | S10-03 (F2) | use safe output-dir helper |
| 6 | `ui/translation_launcher/worker.py` | M | S10-03 (F2) | use safe output-dir helper |
| 7 | `core/reader_project/recovery.py` | M | S10-03 (F3) | enforce provable artifact ownership (unknown → BLOCK) |

### Tests (7)

| # | Path | Action | Phase | Reason |
|---|---|---|---|---|
| 8 | `tests/integration/test_s10_02_epub_extraction_repair.py` | A | S10-02 | offsets/metadata/positive integration |
| 9 | `tests/e2e/test_s9_07_epub_reader_flow.py` | M | S10-02 | EPUB entry now asserts repaired canonical path |
| 10 | `tests/e2e/test_s10_03_epub_reader_first_e2e.py` | A | S10-03 | full reader-first production E2E |
| 11 | `tests/e2e/test_s10_03_epub_recovery_e2e.py` | A | S10-03 | EPUB recovery/state/isolation E2E |
| 12 | `tests/reader_project/test_recovery.py` | M | S10-03 (F3) | F3 ownership cases + evidence in fixtures |
| 13 | `tests/e2e/test_s9_07_txt_reader_flow.py` | M | S10-03 (F3) | recovery fixtures carry ownership evidence |
| 14 | `tests/e2e/test_s9_07_failure_recovery.py` | M | S10-03 (F3) | recovery fixtures carry ownership evidence |

### Governance artifacts (7)

| # | Path | Action | Phase | Reason |
|---|---|---|---|---|
| 15 | `artifacts/NTPE_S10_01_EPUB_PRODUCTION_PATH_AUDIT.md` | A | S10-01 | audit evidence |
| 16 | `artifacts/NTPE_S10_01_EPUB_PRODUCTION_PATH_DESIGN.md` | A | S10-01 | design evidence |
| 17 | `artifacts/NTPE_S10_02_EPUB_EXTRACTION_REPAIR_REPORT.md` | A | S10-02 | repair evidence |
| 18 | `artifacts/NTPE_S10_03_EPUB_READER_FIRST_E2E_AUDIT.md` | A | S10-03 | E2E audit evidence |
| 19 | `artifacts/NTPE_S10_03_F3_OWNERSHIP_REPAIR_REPORT.md` | A | S10-03 | F3 repair evidence |
| 20 | `artifacts/NTPE_S10_PROGRAM_LEVEL_AUDIT.md` | A | S10 Audit | program audit evidence |
| 21 | `artifacts/NTPE_S10_COMMIT_BOUNDARY.md` | A | S10 Audit | commit boundary manifest |

---

## EXCLUDE — Pre-existing / out-of-scope (5)

These were dirty before S10-01 and are not touched by S10 code. Do not stage.

| # | Path | Status | Reason |
|---|---|---|---|
| 1 | `memory/character_memory_lts.json` | M | pre-existing residual (non-source) |
| 2 | `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | M | S7 literary governance output |
| 3 | `tests/literary/outputs/PS-03/README.md` | D | S7 literary governance output |
| 4 | `tests/literary/outputs/Regression_History.json` | M | S7 literary governance output |
| 5 | `tests/literary/outputs/Regression_History.md` | M | S7 literary governance output |

---

## UNCERTAIN (0)

None.

---

## Notes

- `tests/reader_project/test_recovery.py` contains both S9-06 baseline tests and
  S10-03 F3 additions; the S10-03 additions are the ownership cases and the
  ownership evidence now written by helpers. The file is S10-owned for this
  boundary because S10-03 is the phase that changed its behaviour.
- `tests/e2e/test_s9_07_*.py` are S9-07 files; they are S10-owned only to the
  extent S10-02/S10-03 updated their expectations/fixtures.
- Frozen runtime, provider, model, schema, persistence, and glossary paths are
  absent from the change set (verified).
