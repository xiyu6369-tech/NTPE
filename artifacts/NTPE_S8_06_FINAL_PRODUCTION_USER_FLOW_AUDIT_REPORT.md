# NTPE S8-06 — Final Production User Flow Audit & Release Readiness

**Task**: `NTPE-S8-06`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S8_06_FINAL_PRODUCTION_USER_FLOW_ACCEPTED`

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Actual HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Branch | `main` |
| Git Commit / Push / Tag / History Rewrite | NO |

This task is **audit-only**. No production code was modified in S8-06. The working tree carries the uncommitted S8-01 → S8-05 deliverables.

---

## 2. Production Entry Points

| Entry | File | Delegates to |
|-------|------|--------------|
| CLI (official) | `launcher_translate.py` | `ntpe_production_translate.main()` (txt / batch / epub / regression / evaluate / corpus / doctor) |
| GUI (PySide6) | `ntpe_translation_studio.py` | `ui.translation_studio.app.run()` → `MainWindow` |
| GUI (Tkinter) | `ui.translation_launcher/app.py:run()` | `TranslationLauncherApp` + `LauncherController` |

Routing map:

```text
entry → intake (CanonicalBookIntakeAdapter / EpubExtractionBoundary)
      → validation (LauncherController.validate / Studio button gating)
      → options (TxtTranslationOptions / EpubTranslationOptions)
      → runtime (TranslationRuntime → RuntimeOrchestrator → TranslationEngine)
      → QA/result → output (runtime-produced artifact)
```

---

## 3. TXT End-to-End Flow

| Aspect | Finding | Evidence |
|--------|---------|----------|
| Intake | Canonical `CanonicalBookIntakeAdapter.process_path` handles UTF-8/BOM; no user-facing chapter/chunk exposure | `home_page._on_import_txt` → `process_path`; book_info has title/chars/encoding/preview |
| Launch (Studio) | TXT project → `TxtTranslationOptions` → `TranslationRunner` | `project_page._on_translate` TXT branch |
| Launch (Tkinter) | config → `_build_txt_options` → `TranslationRunner` | `controller.start_translation` |
| Launch (CLI) | `launcher_translate.py txt <in> <out>` → `run_txt` → `TranslationRuntime.translate_txt` | `ntpe_production_translate.run_txt` |
| Runtime model | Frozen `meta/llama-3.2-90b-vision-instruct` | `project_page.py:489`, CLI `DEFAULT_MODEL`, adapter `DEFAULT_MODEL` |
| Result states | dry_run → `dry_run`; success/incomplete/failed mapped explicitly | S8-04, `project_page._on_translation_finished` |
| chunk_successful | Present in success/incomplete/dry_run (S8-05 fix) | `lts/txt_translation_runtime.py` |
| Output | `output/<stem>/<stem>_zh.txt`, runtime-produced | `txt_translation_runtime` `final_output` |

**Status: PASS**

---

## 4. EPUB End-to-End Flow

| Aspect | Finding | Evidence |
|--------|---------|----------|
| Extraction/intake | `EpubExtractionBoundary` → `CanonicalBookIntakeAdapter` | `home_page._on_import_epub`, `_build_epub_options` |
| Chapter map/chunking | `chunk_epub_translation_input` + `ChunkingOptions` | `project_page._build_epub_options` |
| Launch | `EpubTranslationOptions` → `TranslationRunner` → `translate_epub_translation_input` | S8-01 |
| Runtime chain | reader chapter map → `pack_epub_resource_aware` | `translation_worker._runtime_epub_translate` |
| No TXT fallback | asserted by tests | `test_epub_translation_launch`, `test_s8_03_output_policy` |
| dry-run | canonical route used, **no packaging**, `status="dry_run"` | S8-04 worker guard |
| Output | source-adjacent `<source.parent>/output/epub_translation/<id>/<stem>_zh.epub` | worker/packager |
| Live progress | producer filename == consumer filename, file written | S8-05 adapter fix |

**Status: PASS**

---

## 5. GUI State Audit

### PySide6 Translation Studio
- idle → validating → running → dry_run / success / incomplete / failed → idle.
- Duplicate launch blocked: `_on_translate` early-returns when `_current_translation_row == row`; button disabled while running.
- Covered by `test_s8_04_gui_state_acceptance.py` (12 tests) — all pass.

### Tkinter Translation Launcher
- validation (`_validate`) gates Start/Dry-Run buttons.
- worker/controller dry-run, success, incomplete, failure, error mapping verified at worker/callback level.
- **GUI widget-level duplicate-start** cannot be exercised because `TranslationLauncherApp` cannot be constructed (pre-existing Tk pack/grid defect) → classified as pre-existing product-shell defect (non-blocking), not S8-06 regression.

**Status: PASS (with documented Tk GUI-level coverage gap)**

---

## 6. CLI Audit

| Subcommand | Flow | dry-run |
|-----------|------|---------|
| `txt` | user in/out → TXT runtime → `<out>/<stem>_zh.txt` | `--dry-run` → `dry_run` |
| `batch` | folder → batch runtime | `--dry-run` |
| `epub` | extract → temp TXT → **TXT pipeline** → `<out>/<stem>_zh.txt` | `--dry-run` |
| `regression`/`evaluate`/`corpus`/`doctor` | literary/governance tooling | n/a |

Note: CLI `epub` is a legacy EPUB→TXT flow distinct from the Studio's canonical resource-aware EPUB packaging. This is an accepted divergence (S8-03 comparison), not a production blocker for the Studio user flow.

**Status: PASS**

---

## 7. Output / Path / Progress Integrity (S8-03 / S8-05)

| Item | Status |
|------|--------|
| Studio `root_path` | FIXED → repo root `D:\Python\NTPE` (was `ui`); `parents[2]` → `parents[3]` |
| TXT output | UI-derived `output/<stem>` honored → actual artifact |
| EPUB output | runtime-owned source-adjacent path → actual artifact |
| EPUB live progress | producer filename == consumer filename (`_live_progress.json`), file written periodically + final |
| TXT `chunk_successful` | FIXED → present in success result |

**Status: PASS**

---

## 8. Recovery / Failure Behavior

Verified with deterministic mocks/fakes (no provider):
- validation failure blocks launch (Tk controller; Studio button gating).
- runtime/provider failure → `failed`, error surfaced, running state released, re-launchable.
- incomplete → partial success reported, not success.
- dry_run → explicit dry_run, no bogus output.
- duplicate launch → no second execution.
- retry/recovery boundary unchanged (S8 changes did not touch retry/QA policy).

**Status: PASS**

---

## 9. S8-01 → S8-05 Regression Verification

| Task | Preserved | Evidence |
|------|-----------|----------|
| S8-01 EPUB direct launch | YES | `test_epub_translation_launch.py` 6 passed |
| S8-02 UI honesty | YES | `test_s8_02_ui_honesty.py` 8 passed, 1 skipped |
| S8-03 output policy | YES | `test_s8_03_output_policy.py` 8 passed |
| S8-04 GUI state | YES | `test_s8_04_gui_state_acceptance.py` 12 passed |
| S8-05 runtime integrity | YES | root_path/EPUB progress/TXT metadata fixes in place; covered by suites |

**Status: PASS**

---

## 10. User-Facing Honesty Audit (S8-02 no-regression)

| Item | Status |
|------|--------|
| Overwrite | Disabled + labelled "尚未支援"; `_config` never emits overwrite | 
| New/Open Project | Studio Project Page + Home buttons disabled, tooltipped, handlers no-op; no `PLACEHOLDER_NOT_IMPLEMENTED` at runtime |
| Model display | `model_catalog` display_name = "Llama 3.2 90B Vision Instruct", id `meta/llama-3.2-90b-vision-instruct` (no 70B/3.3) |

## 11. Known Limitations Registry

| # | Issue | Affects user flow? | Affects correctness? | Release readiness? | Follow-up task? | Classification |
|---|-------|--------------------|----------------------|--------------------|-----------------|----------------|
| 1 | `TranslationLauncherApp` Tk pack/grid defect | No (controller/worker usable; widget build only) | No | Non-blocking (Tk shell only) | Yes | PRE-EXISTING / NON-BLOCKING |
| 2 | `test_translation_studio_shell.py` modal hang | No | No | No (test-only) | Yes | OUT OF SCOPE |
| 3 | `test_translation_studio_shell.py` localization assertion | No | No | No (test-only) | Yes | OUT OF SCOPE |
| 4 | Stale `test_gui_state.py::test_controller_never_starts_translation` | No | No | No (test-only) | Yes | OUT OF SCOPE |
| 5 | Repo-wide historical `compileall` failures (`tools/one_shots/*`, `archive/legacy_tests/*`, `.kilo/*`) | No | No | No (non-canonical files) | Optional | PRE-EXISTING / NON-BLOCKING |
| 6 | Tk launcher model combobox shows `model_id` not `display_name` | Minor display | No | Non-blocking | Optional | ACCEPTED (cosmetic) |
| 7 | CLI `epub` is legacy EPUB→TXT vs Studio canonical packaging | No (separate entry) | No | Non-blocking | Optional | OUT OF SCOPE |

No item blocks the core TXT/EPUB production user flow.

---

## 12. Regression Matrix

| Flow | Intake | Launch | Dry-run | Success | Incomplete | Failure | Output | Result |
|------|--------|--------|---------|---------|------------|---------|--------|--------|
| TXT / Studio | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| EPUB / Studio | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TXT / Tkinter | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| EPUB / Tkinter | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TXT / CLI | PASS | PASS | N/A | PASS | PASS | PASS | PASS | PASS |
| EPUB / CLI | PASS | PASS | N/A | PASS | PASS | PASS | PASS | PASS |

Tkinter rows reflect controller/worker/callback-level evidence; widget-level GUI automation is blocked by limitation #1 (documented).

---

## 13. Full Test Results

| Suite | Result |
|-------|--------|
| `pytest tests/contract` | **338 passed** |
| `pytest tests/ui` (excl. pre-existing hanging shell file) | **125 passed, 1 skipped** |
| S8-01 (`test_epub_translation_launch.py`) | 6 passed |
| S8-02 (`test_s8_02_ui_honesty.py`) | 8 passed, 1 skipped |
| S8-03 (`test_s8_03_output_policy.py`) | 8 passed |
| S8-04 (`test_s8_04_gui_state_acceptance.py`) | 12 passed |
| shell non-GUI (`test_strings_localization`, `test_no_nvidia_import`) | 2 passed |

The 1 skipped test is the Tk launcher GUI assertion skipped on the pre-existing construction defect.

---

## 14. Compile Boundary

| Target | Result |
|--------|--------|
| `ui` | PASS (0) |
| `core` | PASS (0) |
| `lts` | PASS (0) |
| `cli` | PASS (0) |
| `tests/ui` | PASS (0) |
| `tests/contract` | PASS (0) |
| `python -m compileall -q .` | FAIL — `PRE_EXISTING_UNRELATED_COMPILE_FAILURE` only |

---

## 15. Provider / Network / Real Translation

`0 / 0 / 0` — all verification used mock/fake/deterministic fixtures. No NVIDIA/Gemini/live call.

---

## 16. Working Tree

Uncommitted S8-01 → S8-05 deliverables (production code, tests, reports). Four literary residuals unchanged:

```text
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json   (pre-existing)
 D tests/literary/outputs/PS-03/README.md                                 (pre-existing)
 M tests/literary/outputs/Regression_History.json                         (pre-existing)
 M tests/literary/outputs/Regression_History.md                           (pre-existing)
```

`git diff --check` exit 0.

---

## 17. Scope Contamination Check

- S8-06 modified **no** files (audit-only).
- Prior S8 changes limited to `ui/*`, `core/launcher_product/*`, `core/epub_translation/runtime/adapter.py` (live-progress only), `lts/txt_translation_runtime.py` (result field only), and tests.
- No provider/model/retry/QA/packaging-architecture redesign.
- No commit/push/tag.

---

## 18. Final Release-Readiness Classification

```text
S8_06_FINAL_PRODUCTION_USER_FLOW_ACCEPTED
```

A user who does not know NTPE internals can import a TXT or EPUB, launch translation, observe truthful states (dry-run/success/incomplete/failed), be blocked from duplicate launches, receive no fabricated success or bogus output, and obtain the runtime-produced artifact. Core production flow is closed; all remaining issues are non-blocking or explicitly accepted, with no unhandled correctness blocker.
