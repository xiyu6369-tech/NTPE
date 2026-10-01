# NTPE S8-02 — UI Functional Honesty Cleanup

**Task**: `NTPE-S8-02`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S8_02_UI_FUNCTIONAL_HONESTY_ACCEPTED`

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Actual HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Branch | `main` |
| Git Commit | NO |
| Git Push | NO |
| Git Tag | NO |
| History Rewrite | NO |

---

## 2. Working Tree

### Before S8-02
Four pre-existing literary residuals (untouched) plus the uncommitted S8-01 deliverables:

```text
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
 M ui/translation_studio/pages/project_page.py
 M ui/translation_studio/main_window.py
 M tests/ui/test_translation_launch.py
 M tests/ui/test_translation_launch_gui.py
?? tests/ui/test_epub_translation_launch.py
```

### After S8-02
Same four literary residuals (untouched) + S8-01 deliverables + S8-02 changes:

```text
 M core/launcher_product/model_catalog.py
 M ui/translation_launcher/app.py
 M ui/translation_launcher/state.py
 M ui/translation_studio/pages/home_page.py
 M ui/translation_studio/pages/project_page.py
 M ui/translation_studio/resources/translations.py
?? tests/ui/test_s8_02_ui_honesty.py
```

(The `main_window.py`, `project_page.py` import-fix, and `test_translation_launch*.py` entries visible in `git diff` are carried over S8-01 changes, not S8-02.)

---

## 3. Audit Findings

### Issue 1 — Tkinter launcher `overwrite`
- **Backend truth**: `core/launcher_product/validation.py:124-125` unconditionally blocks `config.overwrite` with `overwrite_not_integrated` ("現有 TXT CLI 沒有 overwrite 參數"). This is the formal product boundary; no safe overwrite runtime exists and no other UI path performs overwrite.
- **UI before**: `ui/translation_launcher/app.py:66` rendered a fully enabled `Overwrite` checkbutton. A user could tick it, and only after Validate/Start would receive `overwrite_not_integrated` — a false-capability flow.
- **Decision**: backend not integrated ⇒ UI must reflect unavailability. No new runtime designed.

### Issue 2 — Translation Studio "新增專案 / 開啟專案"
- **Before**: `ProjectPage._on_new_project()` (`project_page.py:448-451`) opened a `PLACEHOLDER_NOT_IMPLEMENTED` dialog after the user pressed an enabled "新增專案" button. `HomePage._on_new_project()` / `_on_open_project()` silently navigated to the Project page, implying a project could be created/opened. No project persistence system exists.
- **Decision**: no persistence system to be built. Buttons become explicitly unavailable; placeholder dialog removed.

### Issue 3 — Model display name
- **Before**: `core/launcher_product/model_catalog.py:10` listed production model `meta/llama-3.2-90b-vision-instruct` with `display_name="Llama 3.3 70B Instruct"` — misrepresenting the real model.
- **Decision**: display-only correction (model ID, provider route, and runtime selection semantics unchanged).

---

## 4. Changes

| File | Change |
|------|--------|
| `core/launcher_product/model_catalog.py` | `display_name` → `"Llama 3.2 90B Vision Instruct"` (ID/provider unchanged) |
| `ui/translation_launcher/state.py` | Added `overwrite_enabled=False` + `overwrite_disabled_reason` to `LauncherWindowModel` |
| `ui/translation_launcher/app.py` | Overwrite checkbutton disabled + relabelled "Overwrite（尚未支援）"; `_config()` never emits `overwrite=True` when unsupported |
| `ui/translation_studio/resources/translations.py` | New/Open Project labels marked "（尚未支援）"; added `PROJECT_ACTION_NEW`, `UNSUPPORTED_FEATURE_TOOLTIP` |
| `ui/translation_studio/pages/home_page.py` | New/Open Project buttons stored, disabled, tooltipped; handlers made no-ops |
| `ui/translation_studio/pages/project_page.py` | "新增專案" button stored as `btn_new_project`, disabled, tooltipped; placeholder handler removed |
| `tests/ui/test_s8_02_ui_honesty.py` | **NEW** — Tests A–F |

No `core/epub_translation/*`, `lts/txt_translation_runtime.py`, `core/runtime_orchestrator`, `TranslationEngine`, `ProviderManager`, provider, or client file was modified. No production model/provider/retry/QA/packaging/semantics change.

---

## 5. Tests Added (Tests A–F)

`tests/ui/test_s8_02_ui_honesty.py`:
- **A** — `overwrite_enabled is False`; backend still rejects `overwrite=True` (`overwrite_not_integrated`); Tk overwrite control disabled and never emits overwrite.
- **B** — Project Page New Project button disabled, tooltipped, handler shows no placeholder.
- **C** — Home Page New/Open Project buttons disabled, labelled "尚未支援", handlers no-op.
- **D** — production model display metadata contains `3.2`/`90B`, not `3.3`/`70B`; ID/provider unchanged.
- **E** — TXT project remains launchable.
- **F** — EPUB project remains launchable (S8-01 preserved).

All mock/static: provider = 0, network = 0, real translation = 0.

---

## 6. Test Results

| Suite | Result |
|-------|--------|
| `pytest tests/ui/test_s8_02_ui_honesty.py` | **8 passed, 1 skipped** |
| `pytest tests/ui` (excl. pre-existing hanging shell file) | **105 passed, 1 skipped** |
| `pytest tests/contract` | **338 passed** |
| S6 acceptance (within tests/ui) | 37/37 passed |
| `git diff --check` | clean (exit 0) |

Provider = 0 · Network = 0 · Real Translation = 0.

### 6.1 Compile Boundary (S8-02-CLOSURE)

**Repository-wide** `python -m compileall -q .` → **FAIL** (exit 1). Failures are confined **only** to pre-existing unrelated/non-canonical files (see §7.1).

**Canonical production / relevant test compile** (reproducible, per directory):

| Target | Command | Result |
|--------|---------|--------|
| `ui` | `python -m compileall -q ui` | **PASS** (exit 0) |
| `core` | `python -m compileall -q core` | **PASS** (exit 0) |
| `lts` | `python -m compileall -q lts` | **PASS** (exit 0) |
| `cli` | `python -m compileall -q cli` | **PASS** (exit 0) |
| `tests/ui` | `python -m compileall -q tests/ui` | **PASS** (exit 0) |
| `tests/contract` | `python -m compileall -q tests/contract` | **PASS** (exit 0) |

S8-02 touched files verified compilable within the above targets:
`ui/translation_launcher/state.py`, `ui/translation_launcher/app.py`,
`ui/translation_studio/pages/home_page.py`, `ui/translation_studio/pages/project_page.py`,
`ui/translation_studio/resources/translations.py`, `core/launcher_product/model_catalog.py`,
`tests/ui/test_s8_02_ui_honesty.py`.

> Full-repository compileall failure is confined to pre-existing unrelated/non-canonical files and does not affect S8-02 production or test code.

**CLASSIFICATION = `PRE_EXISTING_UNRELATED_COMPILE_FAILURE`**

No file was modified to manufacture a green repository-wide compileall.

---

## 7. Known Pre-existing Issues (NOT S8-02 regressions, NOT fixed)

1. **`compileall -q .` (whole repo) exits 1** — `CLASSIFICATION = PRE_EXISTING_UNRELATED_COMPILE_FAILURE`. Only pre-existing syntactically malformed, unrelated files fail:
   - tracked: `tools/one_shots/{add_function,add_pack_function,apply_fix,fix_b23,inject_pack_func}.py`, `archive/legacy_tests/verify_tqi_effectiveness.py`;
   - ignored agent worktree: `.kilo/worktrees/profuse-pupil/...` (`.gitignore:145` ignores `.kilo/`).
   None are touched by S8-02; the canonical compile boundary (§6.1) passes.
2. **`TranslationLauncherApp` cannot be constructed** — pre-existing Tk geometry defect: `self.status = tk.Text(root, ...)` (`app.py:26`) is gridded while the root also `pack`s a frame (`app.py:46-47`), raising `TclError: cannot use geometry manager grid ... already has slaves managed by pack`. Unrelated to S8-02; not fixed (out of scope). Test A's GUI assertion skips on this defect.
3. **`tests/ui/test_translation_studio_shell.py`** — 5 window tests hang on the blocking `MainWindow.closeEvent` modal (`main_window.py:165`, present at HEAD); 1 localization assertion fails (`歡迎使用` never rendered). Pre-existing; not fixed; deferred to S8-04.
4. **`tests/unit/launcher_product/test_gui_state.py::test_controller_never_starts_translation`** — calls `LauncherController.start_translation()` with no args while the method requires 6; stale test, pre-existing (controller.py unmodified). `tests/unit/launcher_product` is outside the S8-02 modify allowlist, so it was not changed.

---

## 8. Scope Contamination Check

- Modified production files are limited to `ui/translation_launcher/*`, `ui/translation_studio/*`, and `core/launcher_product/*` — all within the S8-02 allowlist.
- No canonical-layer file (EPUB contracts/runtime/adapter/packager, TXT runtime, runtime orchestrator, engine, provider) modified.
- Four literary residuals untouched.
- No new project persistence, no new overwrite architecture, no model migration.
- No `git add` / `commit` / `push` / `tag`.

---

## 9. Final Verdict

```text
S8_02_UI_FUNCTIONAL_HONESTY_ACCEPTED
```

- [x] Overwrite no longer falsely presented as integrated
- [x] New Project no longer fakes a placeholder workflow
- [x] Open Project no longer fakes a placeholder workflow
- [x] Production model display metadata corrected
- [x] S6 TXT flow preserved
- [x] S8-01 EPUB direct launch preserved
- [x] New/modified tests pass
- [x] Scoped compileall PASS (global compileall blocked only by pre-existing malformed files)
- [x] `git diff --check` PASS
- [x] Provider / Network / Real Translation = 0 / 0 / 0
- [x] No unrelated production changes
- [x] No commit / push / tag
- [x] Four literary residuals untouched
- [x] Report created under `artifacts/`
