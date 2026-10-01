# NTPE S8-04 — GUI Dry-Run & Result-State End-to-End Acceptance

**Task**: `NTPE-S8-04`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S8_04_GUI_DRY_RUN_RESULT_STATE_ACCEPTED`

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Actual HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Branch | `main` |
| Commit / Push / Tag / History Rewrite | NO |

---

## 2. Working Tree

### Before S8-04
Four pre-existing literary residuals (untouched) + uncommitted S8-01/S8-02/S8-03 deliverables.

### After S8-04
Same, plus:
- `ui/translation_studio/translation_worker.py`, `ui/translation_studio/pages/project_page.py`, `ui/translation_studio/resources/translations.py` (Studio dry-run result-state)
- `ui/translation_launcher/worker.py` (Tkinter EPUB dry-run guard)
- `tests/ui/test_s8_04_gui_state_acceptance.py` (new)
- `tests/ui/test_s8_03_output_policy.py` (dry-run expectation updated to the corrected contract)

---

## 3. State Model (audited mapping)

| State | Studio (project page) | Studio worker progress | Tkinter result | Tkinter progress |
|-------|-----------------------|------------------------|----------------|------------------|
| idle | no selection / buttons gated | — | buttons normal | — |
| validating | `_on_validate_clicked` (separate) | — | `validate()` gates Start button | — |
| running/translating | `準備中…` → `翻譯中 N/total` | `preparing` / `running` | `啟動翻譯` + disabled | `preparing`/`running` |
| dry_run | **`Dry-Run 已完成`** (fixed) | **`dry_run`** (fixed) | `Dry-Run 完成` | `dry_run` |
| completed/success | `翻譯完成` | `completed` | `翻譯完成` | `completed` |
| incomplete | `翻譯未完成` | `incomplete` | `翻譯未完成` | `incomplete` |
| failed | `翻譯失敗` | `failed` | `翻譯失敗` | `failed` |
| blocked/rejected | duplicate launch → `翻譯已在進行中`; invalid source → disabled | — | disabled buttons / validation | — |

Before S8-04, Studio mapped `status == "dry_run"` to the **failure** branch in both the worker (`_emit_final_progress`) and the project page (`_on_translation_finished`), while `_on_translation_progress` had no dry-run branch. Tkinter already handled dry-run.

---

## 4. PySide6 Translation Studio — State Audit

- **Entry**: `ProjectPage._on_translate()` → `_build_epub_options()`/`TxtTranslationOptions` → `TranslationRunner` → `TranslationWorker`.
- **dry-run**: the Studio UI exposes **no dry-run toggle** (`project_page.py` sets `dry_run=False` for TXT at `:494` and EPUB at `:654`). The dry-run *result contract* is nonetheless now honored end to end (worker + UI), and is exercised by injecting `dry_run` results via mock workers.
- **Routing**: EPUB → `EpubTranslationOptions` → `translate_epub_translation_input` → packaging; no TXT fallback (S8-01 preserved).
- **Duplicate launch**: `_on_translate()` returns early when `self._current_translation_row == row` (`project_page.py:466-469`), and the button is disabled while running.

### 4.1 Fixes applied (Studio, UI layer only)
1. `translation_worker._runtime_epub_translate`: when `options.dry_run` is set, the canonical runtime still runs (no provider in dry-run), but packaging is **skipped** and the worker returns `status="dry_run"` (previously a bogus, empty-translation `.epub` was packaged and reported as success).
2. `translation_worker._emit_final_progress`: added `elif status == "dry_run"` → progress `status="dry_run"`.
3. `project_page._on_translation_progress`: added `dry_run` branch → `Dry-Run 已完成`.
4. `project_page._on_translation_finished`: added `elif status == "dry_run"` → status `Dry-Run 已完成` via `QMessageBox.information` (previously fell through to `翻譯失敗`).
5. `Strings.TRANSLATION_STATUS_DRY_RUN = "Dry-Run 已完成"`.

No provider/network/real translation is invoked in dry-run. No canonical runtime/adapter/packager file was modified.

---

## 5. Tkinter Translation Launcher — State Audit

- **Entry**: `TranslationLauncherApp._start` / `_start_dry_run` → `LauncherController.start_translation(config, ...)` → `ui.translation_launcher.worker.TranslationRunner`.
- **dry-run**: `config.dry_run=True` flows into `TxtTranslationOptions`/`EpubTranslationOptions`; the worker's `_emit_final_progress` already maps `dry_run` correctly, and `app._on_translation_finished` already renders `Dry-Run 完成`.
- **Fix applied**: the Tkinter EPUB worker (`ui/translation_launcher/worker.py`) received the same dry-run guard (skip packaging, return `dry_run`), matching the Studio.
- **Validation failure**: `LauncherController.validate(config)` returns blocking reasons; the Start/Dry-Run buttons are only enabled after a successful `_validate`.
- **Duplicate start**: enforced in the app by disabling Start/Dry-Run during execution; `LauncherController` has no API-level dedup (by design).

---

## 6–10. Result Outcomes (verified by tests)

| Case | Result |
|------|--------|
| Dry-run (TXT) | worker/final progress `dry_run`; UI status `Dry-Run 已完成`; no success/incomplete/failure |
| Dry-run (EPUB) | canonical route used; **no packaging**; `status="dry_run"`, `output=""`, `pipeline_mode="epub"` |
| Success | UI `翻譯完成`; output shown; chunk counts; row/runner reset |
| Incomplete | UI `翻譯未完成`; `2/3 成功`; warning box; not success |
| Failure | UI `翻譯失敗`; critical box; translating state released; project re-launchable |
| Duplicate launch | second `_on_translate()` does not start a second runner (Studio) |

---

## 11. Known Shell/Tk Blockers (pre-existing, not fixed)

- `TranslationLauncherApp` cannot be constructed: pre-existing Tk `pack`/`grid` defect (`app.py:26` `self.status = tk.Text(root, …)` gridded while root packs a frame). Consequence: **GUI-widget-level** Tkinter tests cannot run.
  - Mitigation: Tkinter result/state callbacks are exercised against a minimal stand-in receiver (unbound method calls); worker/controller/model tested directly. **Test J (duplicate start) is a documented GUI-level coverage gap** — prevention is widget-state-based and cannot be exercised without constructing the app.
- `tests/ui/test_translation_studio_shell.py`: `MainWindow.closeEvent` blocking-modal hang + `歡迎使用` localization assertion failure — shell lifecycle, outside S8-04 (state/result) scope; not fixed.
- Repo-wide `compileall -q .` still fails only on pre-existing unrelated malformed files (`tools/one_shots/*`, `archive/legacy_tests/*`, ignored `.kilo/`) — `PRE_EXISTING_UNRELATED_COMPILE_FAILURE`.

---

## 12. S8-03 Discovered Issues — Impact Assessment (DOCUMENT ONLY, not fixed)

| # | Issue | Affects dry-run? | Affects result-state correctness? | Wrong state shown? | S8-04 blocker? | Separate task? |
|---|-------|------------------|-----------------------------------|--------------------|----------------|----------------|
| A | Studio `root_path = parents[2]` → `D:\Python\NTPE\ui` | No (dry-run state unaffected) | Indirect only: `output`/`output_dir` values land under `ui/...`; status mapping unaffected | No — UI shows the true artifact path; location is surprising | No | **Yes (S8-05)** — changes output locations + runtime config lookup |
| B | EPUB live-progress filename mismatch (`_live_progress.json` polled vs `_epub_live_progress.json` written) | No | No terminal-state effect | Mid-run progress may not stream for EPUB; final state correct | No | **Yes (S8-05)** |
| C | TXT success result lacks `chunk_successful` | No | Minor: TXT success shows `成功區塊：0 / N` (status still `success`) | Mildly misleading count, not a false status | No | **Yes (S8-05)** — fix lives in `lts` canonical runtime |

All three are **DOCUMENT ONLY** for S8-04.

---

## 13. Tests

New: `tests/ui/test_s8_04_gui_state_acceptance.py` (12 tests)
- **A** Studio TXT dry-run → `dry_run` (worker + UI).
- **B** Studio EPUB dry-run → canonical route, no packaging, `dry_run`.
- **C** Studio success state.
- **D** Studio incomplete state.
- **E** Studio failure state (+ translating state released, re-launchable).
- **F** Studio duplicate launch blocked.
- **G** Tkinter dry-run state (worker `_emit_final_progress` + app callback).
- **H** Tkinter validation failure blocks.
- **I** Tkinter success/failure/error mapping.
- **J** Tkinter duplicate start — documented GUI-level coverage gap.

Updated: `tests/ui/test_s8_03_output_policy.py::test_c_dry_run_is_not_success_or_incomplete` now expects the corrected `dry_run` state.

All mock/fake: Provider = 0 · Network = 0 · Real Translation = 0.

---

## 14. Canonical Compile Boundary

| Target | Result |
|--------|--------|
| `python -m compileall -q ui` | PASS (0) |
| `python -m compileall -q core` | PASS (0) |
| `python -m compileall -q lts` | PASS (0) |
| `python -m compileall -q cli` | PASS (0) |
| `python -m compileall -q tests/ui` | PASS (0) |
| `python -m compileall -q tests/contract` | PASS (0) |
| `python -m compileall -q .` (repo-wide) | FAIL (1) — pre-existing unrelated only |

Regression: `pytest tests/ui` (excl. pre-existing hanging shell file) = **125 passed, 1 skipped**; `pytest tests/contract` = **338 passed**; S6 TXT and S8-01 EPUB suites preserved.

---

## 15. `git diff --check`

Exit 0 (clean; only CRLF informational warnings).

---

## 16. Provider / Network / Real Translation

`0 / 0 / 0` — all verification used fake/mock runtimes.

---

## 17. Scope Contamination Check

- Production changes limited to `ui/translation_studio/*` and `ui/translation_launcher/worker.py` (UI layer).
- No `core/epub_translation/*`, `lts/txt_translation_runtime.py`, `TranslationEngine`, `RuntimeOrchestrator`, provider, model, retry/QA, or packaging change.
- No Tk layout repair, no shell redesign, no project persistence, no output-policy redesign.
- Four literary residuals untouched.
- No commit / push / tag.

---

## 18. Final Verdict

```text
S8_04_GUI_DRY_RUN_RESULT_STATE_ACCEPTED
```

- [x] Studio TXT dry-run state correct
- [x] Studio EPUB dry-run state correct (canonical route, no packaging)
- [x] EPUB remains canonical EPUB route (no TXT fallback)
- [x] Success result maps correctly
- [x] Incomplete result maps correctly
- [x] Failure result maps correctly
- [x] Duplicate launch blocked (Studio)
- [x] Tkinter dry-run/result state verified at worker/callback level; GUI widget-level duplicate-start documented as blocked by the pre-existing Tk construction defect
- [x] No provider / network / real translation
- [x] S6 TXT preserved; S8-01 EPUB preserved
- [x] Canonical compile boundary PASS
- [x] `git diff --check` PASS
- [x] No unrelated production changes
- [x] Four literary residuals untouched
- [x] No commit / push / tag
- [x] Report artifact created
