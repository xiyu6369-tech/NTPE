# NTPE S10 Program-Level Audit

Baseline HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e` (tag `s9-complete`)
Actual HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e`
Branch: `main`
Tag: `s9-complete`

Status: S10 PROGRAM AUDIT COMPLETE (no commit / push / tag)

All S10 work is uncommitted and strictly after the S9 boundary `4a539b8`.

---

## 1. Phase Reverification (from current worktree)

| Phase | Artifacts | Result | Evidence |
|---|---|---|---|
| S10-01 | `NTPE_S10_01_EPUB_PRODUCTION_PATH_AUDIT.md`, `..._DESIGN.md` | PASS | F1 classified as Extraction Contract Defect; no production change |
| S10-02 | `NTPE_S10_02_EPUB_EXTRACTION_REPAIR_REPORT.md` | PASS | body offsets, chapter slices, metadata handoff, positive integration |
| S10-03 | `NTPE_S10_03_EPUB_READER_FIRST_E2E_AUDIT.md`, `NTPE_S10_03_F3_OWNERSHIP_REPAIR_REPORT.md` | PASS | F2 + F3 closed; full reader journey passes |

Reverified by re-executing tests from the worktree, not by copying reports.

---

## 2. Closure Ledger

### F1 — CLOSED (Extraction Contract Defect)
`EpubExtractionBoundary` now populates `body_start_offset`/`body_end_offset`;
the canonical path `extraction -> intake -> EpubTranslationInput -> chunk_epub_translation_input`
succeeds. Evidence: `tests/integration/test_s10_02_epub_extraction_repair.py`.

### F2 — CLOSED (Output Path Contract Defect)
`core/epub_translation/output_layout.py` is a pure, deterministic, cross-platform
safe helper used by the EPUB adapter and both UI workers. The raw identifier
(`urn:uuid:...`) is preserved in EPUB metadata; only the filesystem directory
segment is sanitized. No source-identity mutation. Evidence:
`test_e2e_identifier_yields_filesystem_safe_output_dir`, URN-identifier journey.

### F3 — CLOSED (Recovery Binding Contract Defect)
`core/reader_project/recovery.py` enforces provable ownership:
- valid project + source ownership → eligible
- wrong project (output_dir mismatch) → BLOCK
- wrong source (input mismatch) → BLOCK
- missing `output_dir` evidence → BLOCK
- missing `input` evidence → BLOCK
- insufficient evidence (no completed chunks) → BLOCK
Evidence fields are the existing runtime writer fields (`input`, `output_dir`);
no new artifact registry/schema/database. Evidence:
`tests/reader_project/test_recovery.py` (7 F3 cases) and
`tests/e2e/test_s10_03_epub_recovery_e2e.py`.

---

## 3. Deferred Items (unchanged)

| Item | Status | Confirmation |
|---|---|---|
| S3 non-linear spine ordering | DEFERRED | Not S10-caused, not modified, not required by the accepted all-linear fixtures |
| TOC title fallback | DEFERRED | Not S10-caused, not modified; fixtures supply in-document `<h1>` titles |

Neither was silently promoted to CLOSED.

---

## 4. Full EPUB Production Flow (boundary → implementation → test)

```
EPUB                         (fixture)
 -> Extraction               core/adapters/epub_extraction_boundary.py      S10-02 tests
 -> Intake                   core/adapters/canonical_book_intake_adapter.py S10-02 tests
 -> EpubTranslationInput      ui/.../project_page.py + launcher             S10-03 journey
 -> Chunking                  core/epub_translation/chunking.py             S10-02 tests
 -> Translation Entry         ui/translation_studio/pages/project_page.py   S10-03 journey
 -> TranslationRunner         ui/translation_studio/translation_worker.py   S10-03 journey
 -> Injected runtime          [SEAM] deterministic_epub_runtime              S10-03
 -> EPUB Packaging            core/epub_translation/runtime/epub_packager.py S10-03 journey
 -> Final EPUB                tests read the produced archive                S10-03 journey
 -> Project persistence       _persist_translation_result                   S10-03 journey
 -> Open Result               result_opener (fake)                          S10-03 journey
 -> Restart / Restore         new ProjectPage + manager                     S10-03 journey
 -> Recovery                  core/reader_project/recovery.py               F3 tests + recovery E2E
```

## 5. Real vs Injected Boundary

Real production integration: Extraction, Intake, EpubTranslationInput, Chunking,
Translation Entry, Packaging, Project persistence, Output path, Recovery
validation.

Injected/fake external boundary: provider / network / real translation (patched
runtime execution) and OS opener / modal dialogs.

Provider Execution = 0, Network Execution = 0, Real Translation = 0.

---

## 6. Boundaries

- Frozen runtime (`TranslationRuntime`, `RuntimeOrchestrator`, `TranslationEngine`,
  `ProviderManager`, `NvidiaTranslationProvider`, `NvidiaClient`) — UNCHANGED
  (`git diff 4a539b8 --name-only` shows no such paths).
- Model `meta/llama-3.2-90b-vision-instruct` — UNCHANGED.
- `ReaderProject` schema v1 and `core/reader_project/models.py|store.py|identity.py`
  — UNCHANGED.
- No second persistence, no second EPUB pipeline, no artifact/source/recovery
  registry.
- Glossary — NOT IMPLEMENTED.
- S7 literary governance and `tests/literary/outputs/**` — untouched.
- Security: `_validate_zip_security` and path normalization untouched; F2
  sanitization is filesystem-only, never metadata.

---

## 7. Test Evidence (single runs, current worktree, `QT_QPA_PLATFORM=offscreen`)

```
S10 + S9 reader (tests/e2e + tests/reader_project + S10-02 integration): 117 passed
Combined S9/S10 regression (contract s1..s5c + unit extraction + integration
  + ui epub/s8/s9):                                                      455 passed, 1 skipped
S6-03 acceptance (isolated):                                             7 passed
```

Phase-specific:
- S10-02: `tests/integration/test_s10_02_epub_extraction_repair.py` 4 passed
- S10-03: `tests/e2e/test_s10_03_epub_reader_first_e2e.py` + `..._recovery_e2e.py` 18 passed
- F3: `tests/reader_project/test_recovery.py` + 7 new cases (68 passed in dir)

### Pre-existing failures (re-confirmed, fresh evidence)

| Suite | Count | Classification | Evidence |
|---|---|---|---|
| `tests/unit/translation_release/reader_structure/test_epub_packager.py` | 3 failed | D. environment-sensitive | `assert result is False` fails because `epub.write_epub` does not raise on this Windows/env; exercised module untouched by S10 |
| `tests/lts_stage_01` | 3 failed | E. stale legacy | missing root script `ntpe_translate_txt.py`; stale prompt format; stale dry-run status expectation; exercised `lts/txt_translation_runtime.py` untouched by S10 |

No failure classifies as A (S10 regression) or B (S9 regression).

---

## 8. S9 Regression

Reader-project, S9-03/04/05 UI, S9-06 recovery, S9-07 TXT/EPUB reader flows all
pass. S9 boundary `s9-complete` (4a539b8) is unmodified.

## 9. TXT Safety

`TXT Impact = NONE`. `lts/txt_translation_runtime.py` and `translate_txt` are
unchanged; TXT start/resume/output/project-persistence flows pass. The only
shared file touched is `core/reader_project/recovery.py`, whose change *tightens*
artifact ownership for both formats using evidence both writers already emit.

---

## 10. Repository Hygiene

- `artifacts/` — governance evidence only.
- `tests/` — test code.
- No root scratch files, temporary EPUBs, debug logs, or random JSON.
- Pre-existing residuals untouched: `memory/character_memory_lts.json`,
  the four `tests/literary/outputs/*` entries.

## 11. Attribution

Exact per-path attribution is in `artifacts/NTPE_S10_COMMIT_BOUNDARY.md`.
INCLUDE = 21, EXCLUDE = 5, UNCERTAIN = 0.

## 12. Stop Conditions

NONE.
