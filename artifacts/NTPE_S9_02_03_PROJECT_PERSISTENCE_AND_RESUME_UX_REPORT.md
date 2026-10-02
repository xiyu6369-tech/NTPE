# NTPE S9-02 / S9-03 — Persistent Project & Resume UX Report

**Tasks**: `NTPE-S9-02`, `NTPE-S9-03` (backend + UI)
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S9_02_COMPLETE`, `S9_03_COMPLETE`
**Governance**: no S9 commit / push / tag. Provider = 0, Network = 0, Real Translation = 0.

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| HEAD | `914a847` (`feat(ui): S8 reader-first studio honesty and result integrity`) |
| Branch | `main` |
| S8 worktree | committed (owner-approved), 23 files |
| S9 files | uncommitted (new, untracked) |
| Literary residuals | **untouched** (per owner: leave as-is) |

---

## 2. S9-02 — Persistent Book Project

New package `core/reader_project/` (TXT/EPUB shared model, S9 §4/§7/§12/§19/§20):

| File | Responsibility |
|------|----------------|
| `models.py` | `ReaderProject` + schema v1 (`project_schema_version=1`), `ReaderStatus` enum, section records |
| `identity.py` | canonical source identity (TXT `sha256[:16]`, EPUB `sha256`), change detection |
| `store.py` | `NTPE_HOME` resolution (`%LOCALAPPDATA%\NTPE` / XDG / `~/.ntpe`), atomic JSON write, path-traversal guards |
| `manager.py` | `create / load / save / update / list_projects / delete` |

Key properties:

- **No second checkpoint engine** — runtime resume/artifacts are referenced only.
- **Atomic writes** (temp file + `os.replace` + `fsync`) for Project state.
- **Schema versioning** — newer schema rejected, older routed through a migration table (empty for v1).
- **Delete** requires `confirm=True`, scoped to one project dir; never touches sources/outputs/other projects.
- **Storage is never CWD/repo-relative** (fixes S9 §19 gap for TXT output selection).

Tests: `tests/reader_project/test_project_identity.py`, `test_project_store.py` (24 tests).

---

## 3. S9-03 — Resume / Interrupted State UX

### Backend
- `core/reader_project/state.py` — derives `ReaderStatus` from the runtime
  `*_resume_state.json` + artifact presence + source identity, never rewriting
  runtime state. Handles `not_started / resumable / completed / incomplete /
  failed / source_changed / unrecoverable`.
- `core/reader_project/labels.py` — Traditional-Chinese reader labels and primary
  actions (`繼續翻譯`, `開啟成品`, `來源已變更`, …); no raw runtime status leaks.

### UI (additive — preserves all S8-asserted behavior)
- `ui/translation_studio/pages/project_page.py`
  - injectable `ReaderProjectManager`; `refresh_projects()` renders the reader
    library from persisted storage;
  - `add_project` persists a Project only when the source file actually exists;
    otherwise keeps the legacy in-memory behavior (S8 tests unchanged);
  - TXT resume/launch for persisted projects uses an **absolute** project-owned
    output dir (`<NTPE_HOME>/output/<project_id>`) instead of CWD-relative
    `output/<stem>`;
  - `_persist_translation_result` records the **runtime-returned** artifact path
    (never guessed) and derived reader state; errors mark the project `failed`.
- `ui/translation_studio/main_window.py` — creates the manager and restores
  projects on startup (guarded; failures never break the shell).

Tests: `tests/reader_project/test_resume_state.py`, `tests/ui/test_s9_03_resume_ux.py`.

---

## 4. Validation Evidence

```
tests/reader_project tests/ui/test_s9_03_resume_ux.py
tests/ui/test_s8_02_ui_honesty.py tests/ui/test_s8_03_output_policy.py
tests/ui/test_s8_04_gui_state_acceptance.py
=> 70 passed, 1 skipped
```

Qt run with `QT_QPA_PLATFORM=offscreen`. No provider/network/real translation.

---

## 5. Pre-existing Issue (recorded, not fixed — outside S9 scope)

`tests/ui/test_translation_studio_shell.py` hangs at `window.close()` because
`MainWindow.closeEvent` opens an unpatched `QMessageBox.question` confirmation
(`MSG_CONFIRM_CLOSE`). Verified: with the dialog patched, close returns in
0.01s; the `closeEvent` code is unchanged from HEAD and the S9 diff to
`main_window.py` only adds the startup-refresh block. This is test-infrastructure
drift, not an S9 regression. S9 validation avoids the hanging suite.

---

## 6. Constraints Honored

- Frozen runtime untouched: `lts/**`, `core/epub_translation/**`,
  `core/translation_runtime/**`, `core/runtime_orchestrator/**`,
  `core/translation_engine/**`.
- No second translation/checkpoint engine.
- Four literary residuals untouched.
- No S9 commit / push / tag.

---

## 7. Remaining

`S9-04` Reader Progress Dashboard, `S9-05` Completion & Output UX,
`S9-06` Recovery & Source Integrity, `S9-07` Reader-First E2E Acceptance.

**Note:** the full card-based "我的小說" library (S9 §9) supersedes the current
table and S8 honesty assertions (`New/Open Project` disabled). That migration
should be done deliberately in S9-04 with the affected S8 tests updated.
