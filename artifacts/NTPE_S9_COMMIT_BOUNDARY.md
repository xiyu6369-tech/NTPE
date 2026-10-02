# NTPE S9 — Commit Boundary

**Task**: S9 Commit Boundary Definition (pre-commit)
**Date**: 2026-10-02
**Baseline**: `914a847`
**Governance**: This document defines the boundary only. No commit / push / tag is performed.

---

## 1. Principle

```
S9 Commit = exactly S9-owned changes + required S9 governance artifacts
            - pre-existing unrelated state
```

No "commit everything". No commit of code that omits required S9 evidence.

---

## 2. INCLUDE (S9-owned) — 42 paths

### 2.1 Modified tracked (5) — S9

| Path | Phase |
|------|-------|
| `ui/translation_studio/main_window.py` | S9-03/04 |
| `ui/translation_studio/pages/home_page.py` | S9-04 |
| `ui/translation_studio/pages/project_page.py` | S9-03/04/05/06 |
| `ui/translation_studio/resources/translations.py` | S9-04/05/06 |
| `tests/ui/test_s8_02_ui_honesty.py` | S9-04 (assertion migration only) |

### 2.2 Untracked production (12)

```
core/reader_project/__init__.py
core/reader_project/identity.py
core/reader_project/labels.py
core/reader_project/manager.py
core/reader_project/models.py
core/reader_project/recovery.py
core/reader_project/state.py
core/reader_project/store.py
ui/translation_studio/project_view_model.py
ui/translation_studio/result_opener.py
ui/translation_studio/widgets/__init__.py
ui/translation_studio/widgets/project_card.py
```

### 2.3 Untracked tests (11)

```
tests/reader_project/test_project_identity.py
tests/reader_project/test_project_store.py
tests/reader_project/test_recovery.py
tests/reader_project/test_resume_state.py
tests/e2e/conftest.py
tests/e2e/test_s9_07_txt_reader_flow.py
tests/e2e/test_s9_07_epub_reader_flow.py
tests/e2e/test_s9_07_failure_recovery.py
tests/ui/test_s9_03_resume_ux.py
tests/ui/test_s9_04_dashboard.py
tests/ui/test_s9_05_completion_output.py
```

### 2.4 Untracked governance artifacts (14)

```
artifacts/NTPE_S9_01_PROJECT_PERSISTENCE_AUDIT_AND_DESIGN.md
artifacts/NTPE_S9_02_03_PROJECT_PERSISTENCE_AND_RESUME_UX_REPORT.md
artifacts/NTPE_S9_04_READER_PROGRESS_DASHBOARD_REPORT.md
artifacts/NTPE_S9_05_COMPLETION_OUTPUT_UX_REPORT.md
artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_AUDIT.md
artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_CONTRACT.md
artifacts/NTPE_S9_06_PHASE_C_REPAIR_AUDIT.md
artifacts/NTPE_S9_06_PHASE_C_REPAIR_REPORT.md
artifacts/NTPE_S9_06_PHASE_D_VERIFICATION_REPORT.md
artifacts/NTPE_S9_07_READER_FIRST_E2E_AUDIT.md
artifacts/NTPE_S9_07_FINDINGS.md
artifacts/NTPE_S9_07_READER_FIRST_E2E_ACCEPTANCE_REPORT.md
artifacts/NTPE_S9_PROGRAM_LEVEL_AUDIT.md
artifacts/NTPE_S9_COMMIT_BOUNDARY.md
```

---

## 3. EXCLUDE (pre-existing / non-S9)

| Path | Status | Reason |
|------|--------|--------|
| `tests/literary/outputs/PS-03/README.md` | D | Pre-existing deletion; literary residual governance. Not touched by S9. |
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | M | Pre-existing literary residual modification. |
| `tests/literary/outputs/Regression_History.json` | M | Pre-existing literary residual modification. |
| `tests/literary/outputs/Regression_History.md` | M | Pre-existing literary residual modification. |

No shell-test repair is included: `tests/ui/test_translation_studio_shell.py` is **unmodified**
(pre-existing hang, out-of-scope).

No F1-related code is included: F1 is DEFERRED; no EPUB extraction/chunking file changed.

No unrelated refactors, diagnostics, or root scratch files are present.

---

## 4. Attribution completeness

| Category | Count |
|----------|-------|
| INCLUDE | 42 |
| EXCLUDE | 4 |
| **UNCERTAIN** | **0** |

Every modified, added, and deleted path is classified. No `UNKNOWN`.

### Count reconciliation

```
5 (modified tracked S9)
+ 12 (untracked production)
+ 11 (untracked tests)
+ 14 (untracked artifacts)
= 42  INCLUDE
+ 4   EXCLUDE (pre-existing literary residuals)
= 46  dirty paths total
```

The earlier "43" was an arithmetic error (the §2.4/§6 manifests already totalled 42).
Corrected count: **42 INCLUDE**. The manifest in §6 matches `git diff --cached --name-only`
after staging (verified in the Final Commit task).

---

## 5. Verification before commit (future task)

The future "S9 Final Commit" task must:
1. `git add` exactly the INCLUDE paths (never `git add -A`).
2. Confirm `git status` shows only EXCLUDE paths left dirty (literary residuals).
3. Run the regression set (S9-03/04/05/06/07 + S8-02/03/04) → expect 151 passed, 1 skipped.
4. Commit; then inspect; then push; then tag (separate authorization).

---

## 6. S9 Commit Candidate Manifest

```
INCLUDE: (42)
  ui/translation_studio/main_window.py
  ui/translation_studio/pages/home_page.py
  ui/translation_studio/pages/project_page.py
  ui/translation_studio/resources/translations.py
  ui/translation_studio/project_view_model.py
  ui/translation_studio/result_opener.py
  ui/translation_studio/widgets/__init__.py
  ui/translation_studio/widgets/project_card.py
  core/reader_project/__init__.py
  core/reader_project/identity.py
  core/reader_project/labels.py
  core/reader_project/manager.py
  core/reader_project/models.py
  core/reader_project/recovery.py
  core/reader_project/state.py
  core/reader_project/store.py
  tests/ui/test_s8_02_ui_honesty.py
  tests/ui/test_s9_03_resume_ux.py
  tests/ui/test_s9_04_dashboard.py
  tests/ui/test_s9_05_completion_output.py
  tests/reader_project/test_project_identity.py
  tests/reader_project/test_project_store.py
  tests/reader_project/test_recovery.py
  tests/reader_project/test_resume_state.py
  tests/e2e/conftest.py
  tests/e2e/test_s9_07_txt_reader_flow.py
  tests/e2e/test_s9_07_epub_reader_flow.py
  tests/e2e/test_s9_07_failure_recovery.py
  artifacts/NTPE_S9_01_PROJECT_PERSISTENCE_AUDIT_AND_DESIGN.md
  artifacts/NTPE_S9_02_03_PROJECT_PERSISTENCE_AND_RESUME_UX_REPORT.md
  artifacts/NTPE_S9_04_READER_PROGRESS_DASHBOARD_REPORT.md
  artifacts/NTPE_S9_05_COMPLETION_OUTPUT_UX_REPORT.md
  artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_AUDIT.md
  artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_CONTRACT.md
  artifacts/NTPE_S9_06_PHASE_C_REPAIR_AUDIT.md
  artifacts/NTPE_S9_06_PHASE_C_REPAIR_REPORT.md
  artifacts/NTPE_S9_06_PHASE_D_VERIFICATION_REPORT.md
  artifacts/NTPE_S9_07_READER_FIRST_E2E_AUDIT.md
  artifacts/NTPE_S9_07_FINDINGS.md
  artifacts/NTPE_S9_07_READER_FIRST_E2E_ACCEPTANCE_REPORT.md
  artifacts/NTPE_S9_PROGRAM_LEVEL_AUDIT.md
  artifacts/NTPE_S9_COMMIT_BOUNDARY.md

EXCLUDE: (4)
  tests/literary/outputs/PS-03/README.md                          (pre-existing deletion)
  tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json  (pre-existing)
  tests/literary/outputs/Regression_History.json                  (pre-existing)
  tests/literary/outputs/Regression_History.md                    (pre-existing)

UNCERTAIN: 0
COMMIT CANDIDATE: READY
```

---

## 7. Status

Commit Candidate: **READY** · UNCERTAIN files: **0**.
No commit / push / tag performed. Awaiting the separate "S9 Final Commit" task.
