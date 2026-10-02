# NTPE S9-04 — Reader Progress Dashboard / Project Card Library Report

**Task**: `NTPE-S9-04`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S9_04_COMPLETE`
**Governance**: no commit / push / tag. Provider = 0, Network = 0, Real Translation = 0.

---

## S9-04 IMPLEMENTATION REPORT

**Baseline HEAD**: `914a847`
**Actual HEAD**: `914a847` (no S9 commit)

### Files added
- `ui/translation_studio/project_view_model.py` — Qt-free card view model; reuses
  canonical `state.derive_state` + `labels` (no second reader-state system).
- `ui/translation_studio/widgets/__init__.py`
- `ui/translation_studio/widgets/project_card.py` — `ProjectCard` (status, progress,
  action, delete, missing-source/error note).
- `tests/ui/test_s9_04_dashboard.py` — 19 dashboard tests.
- `artifacts/NTPE_S9_04_READER_PROGRESS_DASHBOARD_REPORT.md`

### Files modified
- `ui/translation_studio/pages/project_page.py` — card library; New/Open/Delete;
  real lifecycle via injected manager; hidden S8-compat table retained as the
  translation workspace/data layer.
- `ui/translation_studio/pages/home_page.py` — New/Open enabled and emit real
  `new_project_requested` / `open_project_requested` signals.
- `ui/translation_studio/main_window.py` — 首頁 New → `ProjectPage.new_project()`;
  Open → 我的小說 library.
- `ui/translation_studio/resources/translations.py` — library/empty/new/delete strings.
- `tests/ui/test_s8_02_ui_honesty.py` — Tests B/C precisely migrated (§11).

### Files deleted
- None.

### Results

| Item | Result |
|------|--------|
| Project dashboard | PASS |
| Project card library | PASS |
| New Project | PASS |
| Open Project | PASS |
| Resume | PASS |
| Source identity | PASS |
| Delete | PASS |
| S8 honesty assertion migration | PASS |
| Error handling | PASS |
| Injection | PASS |
| Glossary Import UI | NOT IMPLEMENTED |

### Tests
- Targeted (`tests/reader_project tests/ui/test_s9_03_resume_ux.py tests/ui/test_s9_04_dashboard.py`): **56 passed**
- S9-04 + S8-02/03/04 regression: **84 passed, 1 skipped**
- Broad `tests/ui` (excluding pre-existing hanging shell suite): **147 passed, 1 skipped**
- S8 regression: PASS
- Provider execution: 0 · Network execution: 0 · Real translation: 0
- Frozen runtime modified: NO
- Repository hygiene: PASS
- Commit / Push / Tag: NO

### Pre-existing issues
- `tests/ui/test_translation_studio_shell.py` `window.close()` hang (unpatched
  `QMessageBox.question` in `MainWindow.closeEvent`). Classification unchanged:
  PRE-EXISTING / OUT-OF-SCOPE. Not modified.

### Out-of-scope changes
- None. S9-05/06/07 not started. Glossary Import UI not added.

**FINAL: PASS**

---

## 1. Design

```
UI (ProjectPage cards) → build_card_model (pure) → ReaderProjectManager → ProjectStore
```

- Persistent Project is the single source of truth; the UI never reads `NTPE_HOME`
  or JSON directly (S9-04 §4.1/§12). The manager is injectable; tests use tmp homes.
- Reader status/progress come only from S9-03 `state.derive_state` + `labels`
  (§4.2); the dashboard defines no second derivation.
- Every visible control has a real effect (§4.3): New → `manager.create` + persist;
  Open/Resume → canonical translation/resume path; Delete → `manager.delete(confirm=True)`.
  Completed cards expose no output control (S9-05 owns that) rather than a fake one.

## 2. S8 honesty assertion migration (§11)

| Old (S8) | New (S9-04) |
|----------|-------------|
| New Project exists + disabled | New Project enabled; `new_project()` persists and appears in library |
| Open Project exists + disabled | Open/New enabled; emit real navigation/lifecycle signals |

No test was deleted solely to pass; each old assertion is replaced by a
higher-value real-behavior assertion in `tests/ui/test_s8_02_ui_honesty.py`.

## 3. Notes / follow-ups
- The S8 `QTableWidget` is retained as a hidden compatibility layer so the S8-03/04
  translation/output-policy suites keep passing while the visible surface becomes
  cards. It is data backing, not a visible fake control.
- Translation failure with no runtime resume evidence is displayed via the canonical
  derived status plus a `last_error` note (S9-06 owns full failure/recovery UX).
