# NTPE S9 — Program-Level Audit

**Task**: S9 Program-Level Audit (pre-commit boundary)
**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Governance**: no commit / push / tag. Provider = 0, Network = 0, Real Translation = 0.

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| HEAD | `914a847` |
| Branch | `main` |
| Origin | `origin/main` @ `53138c6` (comparison target only; not used to overwrite local) |
| S9 commit | NONE (all S9 work is uncommitted worktree) |

Baseline `914a847` already contains the owner-approved S8 commit; therefore every
current modification/untracked file is either S9-owned or pre-existing non-S9 drift.

---

## 2. Phase Inventory (verified from current worktree)

| Phase | Artifact(s) | Production | Tests | Status |
|-------|-------------|-----------|-------|--------|
| S9-01 | `NTPE_S9_01_*_AUDIT_AND_DESIGN.md` | design only | — | PASS |
| S9-02 | `NTPE_S9_02_03_*_REPORT.md` | `core/reader_project/{models,identity,store,manager,__init__}.py` | `tests/reader_project/test_project_{identity,store}.py` | PASS |
| S9-03 | (S9-02/03 report) | `core/reader_project/{state,labels}.py`; UI wiring | `tests/reader_project/test_resume_state.py`, `tests/ui/test_s9_03_resume_ux.py` | PASS |
| S9-04 | `NTPE_S9_04_*_REPORT.md` | `project_view_model.py`, `widgets/project_card.py`, `project_page.py`, `home_page.py`, `main_window.py`, `translations.py`; S8-02 assertion migration | `tests/ui/test_s9_04_dashboard.py` | PASS |
| S9-05 | `NTPE_S9_05_*_REPORT.md` | `result_opener.py`, view-model/card output fields | `tests/ui/test_s9_05_completion_output.py` | PASS |
| S9-06 | audit/contract/repair/verification (5 artifacts) | `core/reader_project/recovery.py`; recovery wiring in `_on_resume` | `tests/reader_project/test_recovery.py` | PASS (F1 deferred) |
| S9-07 | audit/findings/acceptance (3 artifacts) | none (E2E only) | `tests/e2e/*` (3 files + conftest) | PASS |

Every phase's `FINAL: PASS` was re-checked against the **current worktree**, not copied from reports.

---

## 3. S9-01 — Problem closure

Design problems defined in S9-01 and their closure:

| S9-01 problem | Closed by | Evidence |
|---------------|-----------|----------|
| Persistent Project entity | S9-02 `ReaderProject` | `core/reader_project/models.py` |
| Source identity | S9-02 `identity.py` | canonical sha256 reuse |
| Project-owned storage | S9-02 `store.py` (`NTPE_HOME`) | atomic writes |
| Atomic Project persistence | S9-02 `store._atomic_write_json` | temp + `os.replace` |
| Resume / recovery boundary | S9-03 `state.py` + S9-06 `recovery.py` | eligibility contract |
| Output ownership | S9-03 project-owned TXT dir + S9-05 output refs | no CWD-relative output |

No open S9-01 finding remains.

---

## 4. S9-02 — Persistence integrity

- `SCHEMA_VERSION = 1` present and unchanged (FROZEN).
- Single persistence boundary: `ProjectStore` writing `<NTPE_HOME>/projects/<id>/project.json` (atomic).
- No second database / checkpoint store added by S9.
- `manager.py` supports create/load/save/update/list/delete.

## 5. S9-03 — Reader state integrity

- `state.py` is the only reader-state derivation.
- `labels.py` is the only zh-TW label source.
- No second reader-state machine introduced by S9-04..S9-07.

## 6. S9-04 — Dashboard

- Card library renders from manager-derived view model.
- S8 `QTableWidget` retained only as hidden compatibility backing (not a second state store).
- S8-02 Tests B/C migrated to real behavior (diff is migration-only).

## 7. S9-05 — Completion / Output

- Output vs runtime recovery artifact are separate dimensions.
- `output exists → recovery eligible` inference: **absent** (verified in tests both directions).
- `ResultOpener` abstraction centralizes OS actions; tests inject a fake.

## 8. S9-06 — Recovery contract traceability (re-verified, not cited)

`core/reader_project/recovery.py` is the sole canonical decision source.

| Contract item | Verified |
|---------------|----------|
| Project identity validation | ✅ |
| Source identity validation | ✅ |
| Source integrity (changed/missing/same-name) | ✅ |
| Runtime artifact (valid/missing/corrupt/incomplete) | ✅ |
| Runtime recoverability | ✅ |
| Recovery eligibility (9 predicates, deterministic) | ✅ |
| `last_error` preservation | ✅ |
| Recovery vs Retry vs Restart (Resume only) | ✅ |
| Atomicity boundary (Project atomic; runtime non-atomic documented) | ✅ |
| Persistence boundary (no second store) | ✅ |
| UI exposure (only when eligible; no fake controls) | ✅ |

- Existing runtime `source_hash` guard: **unchanged** (frozen runtime not modified).
- **Normal Translation ≠ Recovery confirmed**: `_on_translate` (line 939) has **no** recovery gate;
  the recovery gate lives only in `_on_resume` (line 650).

## 9. S9-07 — E2E reproducibility

Reproduced on current worktree:
- `tests/e2e` → **27 passed**
- Combined (reader_project + e2e + S9-03/04/05 UI + S8-02/03/04) → **151 passed, 1 skipped**
- Broad `tests/ui` (excl. pre-existing shell hang) → **160 passed, 1 skipped**

---

## 10. F1 Governance Classification

**F1**: canonical EPUB extraction does not populate chapter body offsets → canonical
`chunk_epub_translation_input` raises → EPUB translation entry cannot complete.

| Question | Answer |
|----------|--------|
| S9-caused? | **NO** (pre-existing; all prior EPUB launch tests mocked `_build_epub_options`) |
| S9-hid? | NO (S9-07 asserts the real failure; no masking) |
| S9 added fake EPUB route? | NO |
| S9 changed frozen runtime to mask? | NO |

**Status: DEFERRED** (pre-existing, outside S9 implementation ownership). Not re-labeled fixed/ignored/resolved.

---

## 11. Pre-existing drift (preserved, not S9-owned)

| Item | Classification |
|------|----------------|
| `tests/literary/outputs/PS-03/README.md` (deleted) | PRE-EXISTING — preserve |
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` (M) | PRE-EXISTING — preserve |
| `tests/literary/outputs/Regression_History.json` (M) | PRE-EXISTING — preserve |
| `tests/literary/outputs/Regression_History.md` (M) | PRE-EXISTING — preserve |
| `tests/ui/test_translation_studio_shell.py` `window.close()` hang | PRE-EXISTING — out-of-scope, unmodified |

S9 did not restore/delete/normalize/rename any residual. No S9 commit may include them.

---

## 12. Governance gates

| Gate | Result |
|------|--------|
| Frozen runtime (`TranslationRuntime`/`RuntimeOrchestrator`/`TranslationEngine`/Provider/NvidiaClient) | **CLEAN** (no diff) |
| Provider execution | 0 |
| Network execution | 0 |
| Real translation | 0 |
| Schema | v1 UNCHANGED |
| Second persistence | NO |
| Glossary (UI/persistence/wiring) | NOT IMPLEMENTED (grep clean) |
| Output ownership | PASS (absolute, project-owned, isolated) |
| Normal Translation / Recovery separation | PASS |
| UI honesty | PASS (all controls REAL / CONDITIONALLY REAL) |
| Repository root hygiene | PASS (no root scratch) |

---

## 13. Worktree attribution summary

| Set | Count | Ownership |
|-----|-------|-----------|
| Modified tracked — S9 | 5 | S9-OWNED |
| Modified tracked — pre-existing | 4 | PRE-EXISTING |
| Deleted tracked — pre-existing | 1 | PRE-EXISTING |
| Untracked — S9 production | 12 | S9-OWNED |
| Untracked — S9 tests | 11 | S9-OWNED |
| Untracked — S9 artifacts | 12 | S9-OWNED |
| UNCERTAIN | **0** | — |

Full per-file attribution and the exact INCLUDE/EXCLUDE set are in
`artifacts/NTPE_S9_COMMIT_BOUNDARY.md`.

---

## 14. Program-Level Acceptance

All §36 criteria satisfied: 7 phases PASS, all artifacts accounted for, full attribution
complete with 0 UNCERTAIN, F1 DEFERRED/pre-existing, literary residuals + shell hang preserved,
frozen runtime clean, schema v1 unchanged, no second persistence, no glossary, output ownership
correct, Normal Translation/Recovery separated, UI honest, full regression PASS, no hidden S9
regression, commit manifest complete. No stop condition triggered.

**Program-Level Audit: PASS** — S9 has a defined, committable boundary (not yet committed).
