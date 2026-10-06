# NTPE S12-03 — Glossary Reader-facing Import UX Report

Reader-facing Glossary workflow wired onto the stable S12-02 backend. No backend,
schema, runtime, provider or model change.

## 0. Baseline

```text
Baseline HEAD : b178f397644fe7ab0dd3a5a5e9489be439aa3d2a
Branch        : main
Actual HEAD   : b178f39 + this commit
Pre-existing dirty state preserved (untouched, not staged): memory/character_memory_lts.json,
four tests/literary/outputs/* residuals (PS-03/README.md still deleted), untracked
S11-01/S11-02 artifacts.
```

## 1. Glossary UI

Added to `ProjectPage` (`ui/translation_studio/pages/project_page.py`), directly under
the toolbar: a `glossaryFrame` with

```text
詞彙表  <status>            [匯入詞彙表] [替換] [解除]
```

- Status is derived from the authoritative `ReaderProject.glossary`, validated through
  `resolve_active_glossary` — never from UI-local state or raw file existence.
- `未設定` when no glossary; `已啟用：<filename>（N 個詞條）` when active and intact;
  `無法使用` when the snapshot is missing/corrupt.
- Buttons: Import always enabled with a selected project; Replace/Detach enabled only
  when a glossary is active. No fake/inert controls; no Save/Apply button (S12-02
  persistence is atomic per operation).
- File filter is `詞彙表 (*.txt *.json)` — CSV not exposed.

## 2. User Flows

- Import: file chooser → `ReaderProjectManager.attach_glossary` (or
  `replace_glossary` when already active) → `refresh_projects` → panel refresh.
- Replace: same path; the backend writes the new content-hash-named snapshot first, then
  updates `project.json`, then collects the old snapshot.
- Detach: confirmation → `detach_glossary` → refresh. Original user file is not deleted.
- Restart: state is re-read from the persisted project; no UI memory is used.
- Invalid import: `GlossaryError` → short reader-safe warning; the project record is
  unchanged (backend state authoritative) and the panel re-renders from it.

## 3. Translation Launch Wiring

All three reader-facing launch sites in `ProjectPage` now bind the current project's
glossary to canonical options via `apply_glossary_to_options`:

- `_on_translate` (TXT and EPUB branches) — binds after options are built, before the
  runner starts.
- `_on_resume` (recovery launch) — same binding.
- `_build_epub_options` — no longer hardcodes `glossary_path=None`; the caller binds.

If the active glossary is unusable (snapshot missing/corrupt), launch is **blocked** with
a warning and no runner is started (never translate with a silently different glossary).

- TXT: `options.glossary_path` → existing `TxtTranslationOptions` → existing
  `load_locked_dictionary`.
- EPUB: `options.glossary_path` → existing `EpubTranslationOptions` → existing adapter
  loader/post-processing.
- `glossary_hash` is set on both option types (S12-02) so the runtime records the
  glossary identity in its resume state for recovery binding.
- No Glossary: `apply_glossary_to_options` returns the options unchanged → feature-off.

## 4. Call-site Audit

```text
ui/translation_studio/pages/project_page.py:707/993/1154  -> FIXED (bound via backend)
ui/translation_launcher/controller.py:46/205              -> LEGACY / INTERNAL (documented)
```

`LauncherController` (`ui/translation_launcher`, reached via `tools/one_shots/ntpe_launcher.py`)
is the separate one-shot launcher product driven by `LauncherConfig`, with no
`ReaderProject` binding; it has no project to attach a glossary to. Its `glossary_path=None`
is an explicit feature-off default for that surface, not the reader-first Project path
(the reader-first entry is `ntpe_translation_studio.py` → `ui.translation_studio`). Left
unchanged per the S12-03 boundary; classified `legacy/internal`.

## 5. Single Source of Truth

The UI keeps no authoritative glossary state. `_load_current_project(row)` resolves the
row's persisted project id through the injected `ReaderProjectManager`; the panel and the
launch binding both read `ReaderProject.glossary`. No second parser, no manual snapshot
writes, no direct JSON edits.

## 6. Error UX / Atomicity

`GlossaryError` (validation/integrity/persistence) is caught and surfaced as a short
message (`GLOSSARY_IMPORT_FAILED_*`, `GLOSSARY_INVALID_*`); diagnostics go to the module
logger. On failure the UI calls `refresh_projects` so it re-renders the unchanged backend
state; the previous glossary (if any) remains active. Detach failure keeps the old glossary.

## 7. Feature-off Behavior

No-glossary projects behave exactly as before: the binder is a no-op, `glossary_path`
stays `None`, and legacy/CLI paths are unchanged. Verified by
`test_k_no_glossary_launch_is_feature_off` and the S9/S10/S11 regression locks.

## 8. Recovery Interaction

No recovery code changed. Because the launch binds `glossary_hash`, the runtime records
it in resume state and the S12-02 recovery gate enforces same-glossary recovery. The UI
does not bypass recovery status/errors.

## 9. Security

The file chooser path is handed to `attach_glossary`/`replace_glossary`, which run the
canonical backend validation (extension allowlist, size cap, strict decode, is-file,
traversal-safe hash-named snapshot). The UI does not copy files, write snapshots, or
bypass any check.

## 10. Tests

`tests/ui/test_s12_03_glossary_ux.py` (13 tests, all pass):

```text
A  no glossary state                 F  replace failure preserves old glossary
B  import valid txt                  G  detach active (confirmed)
C  import valid json                 G2 detach cancelled keeps glossary
D  invalid import unchanged          H  restart/reload preserves glossary
E  replace active glossary           I  TXT launch consumes active glossary
                                     J  EPUB launch consumes active glossary
                                     K  no-glossary launch is feature-off
                                     +  launch blocked when active glossary corrupt
```

Tests mock the file dialog and message boxes and use a capturing fake runner; they do not
mock `ReaderProject` state (they assert persisted manager state and canonical options).

## 11. Regression Results

```text
tests/reader_project + tests/ui/test_s12_03 + S12-02 integration + S11 integration   126 passed
tests/e2e S9-07 txt/epub/failure, S10-03 reader+recovery, S11-04, S11-07             PASS (per-file)
tests/ui (per-file, 18 files)                                                       PASS
  (test_translation_studio_shell.py launches an event loop -> environment-dependent)
unit + contract                                                                     3823 passed / 58 failed / 12 errors
S12-02 glossary backend tests                                                       26 passed
```

## 12. Broad Regression Classification

- S12-03-caused: **none**.
- unit+contract 58 failed identical to S11-11/S12-02 baseline (pre-existing stale
  expectations, `core/quality` optional-import `TypeError`, lts dry-run status).
- Qt whole-directory fatal (tests/ui, tests/e2e) is the pre-existing shared-session
  PySide6/Python 3.14 crash (S11-10 finding); every file passes individually.
- `test_translation_studio_shell.py` is environment-dependent (launches the app event
  loop) — not annotated as a failure.

## 13. Modified Files

```text
ui/translation_studio/pages/project_page.py     (glossary panel + handlers + launch binding)
ui/translation_studio/resources/translations.py (Glossary strings)
tests/ui/test_s12_03_glossary_ux.py             (new)
artifacts/NTPE_S12_03_GLOSSARY_READER_UX_REPORT.md
```

Excluded/untouched: `core/reader_project` backend, `core/epub_translation`,
`lts/txt_translation_runtime.py`, recovery backend, provider, model, `core/glossary.py`,
`core/validator.py`, `engine/`, `core/context/`, `ui/translation_launcher` (legacy),
pre-existing residuals.

## 14. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
```

## 15. S12-03 Acceptance

Import via real backend; txt+json supported; CSV not exposed; status derived from Project;
replace/detach real with failure preservation; restart persistence; invalid input leaves
project unchanged; no fake controls; no second parser/state; TXT and EPUB launch bind
canonical options; no-glossary feature-off unchanged; recovery contract preserved;
security reused; canonical runtime; provider/network/translation 0; backend/schema/legacy
untouched; tests sufficient; hygiene PASS; dirty state preserved.

## 16. Commit

```text
feat(ui): add project glossary workflow
Push origin main · Tag: NO
```
