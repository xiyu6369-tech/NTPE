# NTPE S9-05 — Completion & Output UX Report

**Task**: `NTPE-S9-05`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S9_05_COMPLETE`
**Governance**: no commit / push / tag. Provider = 0, Network = 0, Real Translation = 0.

---

## S9-05 IMPLEMENTATION REPORT

**Baseline HEAD**: `914a847`
**Actual HEAD**: `914a847` (no S9 commit)

### Files added
- `ui/translation_studio/result_opener.py` — `ResultOpener` protocol +
  `SystemResultOpener` (open artifact / reveal folder); returns False on failure,
  never raises.
- `tests/ui/test_s9_05_completion_output.py` — 15 completion/output tests.
- `artifacts/NTPE_S9_05_COMPLETION_OUTPUT_UX_REPORT.md`

### Files modified
- `ui/translation_studio/project_view_model.py` — output presentation fields
  (`output_reference_present`, `output_exists`, `output_kind_label`, `output_name`,
  `output_note`, `can_open_result`, `can_reveal_folder`); completion and output
  availability kept distinct.
- `ui/translation_studio/widgets/project_card.py` — output info block,
  `open_result_requested` / `reveal_folder_requested` signals, "開啟成品" /
  "開啟資料夾" buttons (only when a real output exists).
- `ui/translation_studio/pages/project_page.py` — `set_result_opener`,
  `_on_open_result`, `_on_reveal_folder`; no Project-state mutation on open.
- `ui/translation_studio/resources/translations.py` — completion/output strings.

### Files deleted
- None.

### Results

| Item | Result |
|------|--------|
| Completion UX | PASS |
| Output presentation | PASS |
| Output ownership | PASS |
| Open Result | PASS |
| Output missing handling | PASS |
| Failure presentation | PASS |
| Persistence | PASS |
| Project isolation | PASS |
| S9-04 regression | PASS |
| S8 regression | PASS |

### Tests
- S9-05 targeted + S9-03/04/reader_project regression: **69 passed**
- S8-02/03/04 regression: **28 passed, 1 skipped**
- Broad `tests/ui` (excluding pre-existing hanging shell suite): **160 passed, 1 skipped**
- Provider execution: 0 · Network execution: 0 · Real translation: 0
- Frozen runtime modified: NO
- Glossary Import UI: NOT IMPLEMENTED
- Repository hygiene: PASS
- Commit / Push / Tag: NO

### Pre-existing issues
- `tests/ui/test_translation_studio_shell.py` `window.close()` hang (unpatched
  `QMessageBox.question` in `MainWindow.closeEvent`). Unchanged:
  PRE-EXISTING / OUT-OF-SCOPE. Not modified.

### Out-of-scope changes
- None. No recovery (S9-06), no source integrity, no Glossary.

**FINAL: PASS**

---

## 1. Design

- Completion and output availability are **distinct**: canonical
  `derive_reader_status` governs completion; output availability is a pure
  presentation check on the persisted `output.artifact_path`. No second
  persistent state is created (§4).
- `build_card_model` is the single presentation entry point (§11); the card shows
  output kind/filename and only exposes Open Result when the artifact exists.
- Output stays Project-owned: TXT uses the project-owned absolute output dir
  (S9-03); EPUB keeps the canonical source-adjacent boundary. No CWD-relative path
  is reintroduced (§6/§9).
- `Open Result` uses the injected `ResultOpener` abstraction (§15); ProjectPage
  never calls the OS directly and never mutates Project state on open (§8/§16).

## 2. State matrix

| Reader state | Output ref | Output action |
|--------------|-----------|---------------|
| Not started | — | no result; 開始翻譯 |
| In progress | — | no result; 繼續翻譯 |
| Completed | exists | 開啟成品 + 開啟資料夾 |
| Completed | missing | no result; note 結果檔案不存在 (canonical derivation demotes status) |
| Failed (hard) | — | canonical status + `last_error` note preserved; no result |

## 3. Notes
- A completed project whose artifact is deleted is **not** presented as a normal
  completed result; canonical derivation demotes it and no Open Result is shown.
  Recovery policy is deferred to S9-06.
- Open failure / missing output never modifies the persisted Project; verified by
  byte-comparing `project.json` before/after in tests.
