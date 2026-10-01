# NTPE S8-05 — Runtime Path, Live Progress & Result Metadata Integrity

**Task**: `NTPE-S8-05`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S8_05_RUNTIME_INTEGRITY_REPAIRED_ACCEPTED`

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Actual HEAD | `53138c6caff628d0e9994a458e87e3aef8bec3b0` |
| Branch | `main` |
| Git Commit / Push / Tag / History Rewrite | NO |

---

## 2. Working Tree

### Before S8-05
Four pre-existing literary residuals (untouched) + uncommitted S8-01/02/03/04 deliverables.

### After S8-05
Same, plus:
- `ui/translation_studio/pages/project_page.py` (root_path fix)
- `core/epub_translation/runtime/adapter.py` (live progress filename + writes)
- `lts/txt_translation_runtime.py` (chunk_successful in success result)

---

## 3. Scope A — Studio `root_path` Integrity

### Audit Findings

**Actual problem confirmed**: `project_page.py:530` computed `root_path = Path(__file__).resolve().parents[2]` → `D:\Python\NTPE\ui` (the `ui` directory), not the repository root `D:\Python\NTPE`.

**Impact**:
- `TranslationRuntime(root=ui)` looked for `ui/config/provider_config.json` (does not exist)
- Repo config at `config/provider_config.json` (exists) was never found
- Output paths resolved relative to `ui/` instead of repo root

**Root cause**: `project_page.py` at `ui/translation_studio/pages/project_page.py` needs `parents[3]` (repo root), not `parents[2]` (ui directory). The launcher (`ui/translation_launcher/app.py`) correctly uses `parents[2]` because it sits one level higher.

### Fix Applied

```python
# Before
root_path = Path(__file__).resolve().parents[2]  # → D:\Python\NTPE\ui

# After  
root_path = Path(__file__).resolve().parents[3]  # → D:\Python\NTPE
```

**File**: `ui/translation_studio/pages/project_page.py:530`

**Classification**: `FIXED`

---

## 4. Scope B — EPUB Live Progress Filename & Writes

### Audit Findings

**Producer (adapter)**: `core/epub_translation/runtime/adapter.py:322` defined `live_progress_path = output_dir / f"{stem}_live_progress.json"` (previously `_epub_live_progress.json`) but **never wrote to it**.

**Consumers**: 
- Studio worker `translation_worker.py:55` polls `output_dir / f"{input_stem}_live_progress.json"`
- Tkinter worker `worker.py:64` polls same filename

**Gap**: Adapter defined the path but never wrote to it. Workers polled a file that never existed → EPUB live progress never updated mid-run (only final state appeared).

### Fix Applied

1. **Unified filename**: Changed adapter from `_epub_live_progress.json` → `_live_progress.json` (matches workers) at `adapter.py:322`.
2. **Added live progress writer**: `_save_epub_live_progress(path, payload)` helper (similar to TXT's `save_live_progress`).
3. **Periodic writes**: After each chunk completes, write progress to `live_progress_path` with `status="running"`, `chunk_total`, `chunk_completed`, and message.
4. **Final write**: On session completion, write `status="completed"`, `chunk_completed=total_chunks`.

**Files**:
- `core/epub_translation/runtime/adapter.py`: Added `_save_epub_live_progress`, `total_chunks`/`completed_chunks` tracking, periodic writes in chunk loop, final write on completion.

**Classification**: `FIXED`

---

## 5. Scope C — TXT `chunk_successful` in Success Result

### Audit Findings

**Canonical TXT runtime**: `lts/txt_translation_runtime.py` `translate_txt()` returns three result dicts:
- `dry_run`: has `"chunk_successful": 0` ✓
- `incomplete`: has `"chunk_successful": successful_chunks` ✓
- `success`: **MISSING** `"chunk_successful"` key (only in `summary`)

**UI impact**: `project_page._on_translation_finished` reads `result.get("chunk_successful", 0)` → TXT success showed "成功區塊：0 / N" instead of correct count.

### Fix Applied

Added `"chunk_successful": successful_chunks,` to the success result dict in `lts/txt_translation_runtime.py:1131`.

**File**: `lts/txt_translation_runtime.py:1131`

**Classification**: `FIXED`

---

## 6. Modified Files

| File | Change |
|------|--------|
| `ui/translation_studio/pages/project_page.py` | `parents[2]` → `parents[3]` for correct repo root |
| `core/epub_translation/runtime/adapter.py` | Live progress filename fix + periodic writes + helper |
| `lts/txt_translation_runtime.py` | Added `chunk_successful` to success result |

---

## 7. Test Results

| Suite | Result |
|-------|--------|
| `pytest tests/ui/test_s8_04_gui_state_acceptance.py` | 12 passed |
| `pytest tests/ui/test_s8_03_output_policy.py` | 8 passed |
| `pytest tests/ui` (excl. hanging shell) | 125 passed, 1 skipped |
| `pytest tests/contract` | 338 passed |
| `python -m compileall -q ui/core/lts/cli/tests/ui/tests/contract` | all PASS (exit 0) |
| `git diff --check` | clean (exit 0) |

**Provider / Network / Real Translation**: `0 / 0 / 0`

---

## 8. Pre-existing Issues (unchanged, documented)

- `TranslationLauncherApp` Tk pack/grid defect → GUI tests use stand-in receiver
- `test_translation_studio_shell.py`: blocking modal hang + `歡迎使用` localization failure
- Repo-wide `compileall -q .` fails on pre-existing malformed files (`tools/one_shots/*`, `archive/legacy_tests/*`, ignored `.kilo/`) — `PRE_EXISTING_UNRELATED_COMPILE_FAILURE`
- `test_gui_state.py::test_controller_never_starts_translation` stale signature

---

## 9. Scope Contamination Check

- No canonical runtime/engine/provider/packager changes beyond minimal live progress writes
- No project persistence, output policy redesign, provider/model changes
- No Tk layout repair, shell redesign, project persistence
- Four literary residuals untouched
- No commit / push / tag

---

## 10. Final Verdict

```text
S8_05_RUNTIME_INTEGRITY_REPAIRED_ACCEPTED
```

All three S8-03/S8-04 audit findings resolved with minimal, targeted fixes:

| Scope | Status | Fix Summary |
|-------|--------|-------------|
| A — root_path | **FIXED** | `parents[2]` → `parents[3]` in `project_page.py` |
| B — EPUB live progress | **FIXED** | Filename unified + periodic writes in adapter |
| C — TXT chunk_successful | **FIXED** | Added missing field to success result |

All regression suites pass. No provider/network/real translation executed. No commit/push/tag.