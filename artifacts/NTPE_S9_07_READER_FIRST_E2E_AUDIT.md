# NTPE S9-07 — Reader-First E2E Audit

**Task**: `NTPE-S9-07` (Phase A)
**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Status**: `S9_07_AUDIT_COMPLETE`

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| HEAD | `914a847` |
| Branch | `main` |
| S9-01..S9-06 | uncommitted worktree (preserved) |

---

## 2. Actual Entry Points

### 2.1 Applications
| App | Path | Status |
|-----|------|--------|
| Tkinter Launcher | `ui/translation_launcher/` | Legacy, separate |
| PySide6 Translation Studio | `ui/translation_studio/` | Primary reader UI |

### 2.2 Studio Structure
- `MainWindow`: Home (index 0) + ProjectPage (index 1); startup restore via `ReaderProjectManager`.
- `HomePage`: Import TXT, Import EPUB, New Project, Open Project.
- `ProjectPage`: "我的小說" card library + translation workspace.

---

## 3. Actual Reader Paths

| Path | Location | Canonical? |
|------|----------|-----------|
| TXT import | `HomePage._on_import_txt` → `CanonicalBookIntakeAdapter.process_path` | ✅ canonical |
| EPUB import | `HomePage._on_import_epub` → `EpubExtractionBoundary.extract` | ✅ canonical |
| Project creation | `ProjectPage.new_project` (QFileDialog) → `ReaderProjectManager.create` | ✅ canonical |
| Project persistence | `ProjectPage.add_project` → `_maybe_persist_project` → manager.create | ✅ canonical |
| Project reopen | `MainWindow` startup → `ProjectPage.refresh_projects` → `manager.list_projects` | ✅ canonical |
| TXT translation launch | `ProjectPage._on_translate` → `TxtTranslationOptions` → `TranslationRunner` → `TranslationRuntime.translate_txt` | ✅ canonical |
| EPUB translation launch | `ProjectPage._on_translate` (is_epub) → `_build_epub_options` → `EpubTranslationOptions` → `translate_epub_translation_input` + packager | ✅ canonical |
| Recovery entry | `ProjectCard.resume_requested` → `ProjectPage._on_resume` → `resume=True` | ✅ canonical (S9-06) |
| Output opening | `ProjectCard.open_result_requested` → `ProjectPage._on_open_result` → `ResultOpener` | ✅ canonical (S9-05) |

**Finding E1**: EPUB direct launch **EXISTS** (`_build_epub_options`). EPUB Translation Entry = PASS (not deferred).

---

## 4. Control Audit (No Fake Controls)

| Control | Classification |
|---------|----------------|
| Home · Import TXT | REAL |
| Home · Import EPUB | REAL |
| Home · New Project | REAL |
| Home · Open Project | REAL |
| Project · 我的小說 card | REAL |
| Card · 開始翻譯 (`action_requested`) | REAL |
| Card · 繼續翻譯 (`resume_requested`) | CONDITIONALLY REAL (only when `recovery_eligible`) |
| Card · 開啟成品 / 開啟資料夾 | CONDITIONALLY REAL (only when output exists) |
| Card · 刪除 | REAL |
| Nav · 首頁 / 專案 | REAL |
| HomePage `navigate_to_import_txt/epub` signals | NOT IMPLEMENTED (unused signals, no visible control) |

**Finding C1**: No fake/placeholder controls on the primary reader surface.

---

## 5. Test Seams

| Seam | Location | Use |
|------|----------|-----|
| `ReaderProjectManager(home=tmp)` | `core/reader_project` | Isolated persistent home |
| `ProjectPage.set_project_manager` | S9-03 | Inject tmp manager |
| `ProjectPage.set_result_opener` | S9-05 | Inject fake opener (no OS launch) |
| `patch(...project_page.TranslationRunner)` | S8/S9 tests | Fake runtime; no provider/network |
| `EpubExtractionBoundary` on small fixture | canonical | Offline EPUB extraction |

---

## 6. E2E Plan

Create `tests/e2e/`:
- `conftest.py` — QApplication + `FakeTranslationRunner` + `FakeResultOpener` + EPUB fixture builder
- `test_s9_07_txt_reader_flow.py` — TXT-01..TXT-12
- `test_s9_07_epub_reader_flow.py` — EPUB-01..EPUB-07
- `test_s9_07_failure_recovery.py` — failure UX, missing output, output/runtime separation, isolation, persistence matrix

All deterministic, offline, isolated (tmp NTPE_HOME/source/output), fake runtime.

---

## 7. Stop Condition Check

| Condition | Status |
|-----------|--------|
| Canonical TXT intake available | ✅ |
| Canonical EPUB intake available | ✅ |
| Normal Translation ≠ Recovery | ✅ (S9-06 Repair) |
| Existing runtime resume not bypassed | ✅ |
| source_hash guard intact | ✅ |
| No frozen runtime modification needed | ✅ |
| No provider/network required | ✅ (fake runtime) |

**No stop conditions triggered.** Proceed to E2E implementation.
