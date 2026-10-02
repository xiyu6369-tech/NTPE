# NTPE S9-06 Phase C Repair Report

**Task**: `NTPE-S9-06-Phase-C-Repair`
**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Status**: `S9_06_PHASE_C_REPAIR_COMPLETE`
**Governance**: No commit / push / tag. Provider = 0, Network = 0, Real Translation = 0.

---

## 1. Repair Summary

Fixed the S9-06 Phase C implementation to properly separate **Normal Translation** from **Recovery** and wire the existing runtime resume mechanism.

---

## 2. Issues Fixed

| Issue | Before | After |
|-------|--------|-------|
| Normal Translation gated by recovery eligibility | `_on_translate` blocked when `recovery_eligible=False` | `_on_translate` no longer checks recovery eligibility; new projects can start translation normally |
| No separate Recovery action | Only `action_requested` (used for both "開始翻譯" and "繼續翻譯") | Added `resume_requested` signal and "繼續翻譯" button |
| Recovery action not wired to existing runtime | No separate Recovery action handler | `_on_resume()` calls existing runtime with `resume=True` |
| Recovery eligibility gates Normal Translation | New projects blocked from starting | New projects can start translation normally; Recovery eligibility only gates Recovery action |

---

## 3. Changes Made

### 3.1 project_page.py
- **Removed** recovery eligibility gate from `_on_translate()` (Normal Translation)
- **Added** `_on_resume(project_id)` handler - true Recovery action
- `_on_resume()` validates recovery eligibility, then calls existing runtime with `resume=True`

### 3.2 project_card.py
- Added `resume_requested = Signal(str)` signal
- Added "繼續翻譯" button **only when `recovery_eligible == True`**
- Button emits `resume_requested` signal

### 3.3 project_page.py
- Connected `card.resume_requested.connect(self._on_resume)` in `_add_persisted_project()`
- Removed recovery eligibility gate from `_on_translate()` (Normal Translation)

---

## 4. Behavioral Changes

| Scenario | Before | After |
|----------|--------|-------|
| New project (no runtime artifact) | ❌ Cannot start translation (blocked) | ✅ Can start Normal Translation |
| Existing project, recovery eligible | "開始翻譯" button works | "繼續翻譯" button appears; "開始翻譯" still works for new translation |
| Existing project, recovery blocked | Button disabled/greyed | "繼續翻譯" hidden; recovery badge shows reason; "開始翻譯" still works for new translation |
| Source changed | "開始翻譯" blocked | "繼續翻譯" hidden; "開始翻譯" still works for new translation |

---

## 5. Tests Passing

| Test Suite | Result |
|------------|--------|
| `tests/reader_project` | **61 passed** |
| `tests/ui/test_s9_03_resume_ux.py` | **8 passed** |
| `tests/ui/test_s9_04_dashboard.py` | **14 passed** |
| `tests/ui/test_s9_05_completion_output.py` | **13 passed** |
| `tests/ui/test_s8_02_ui_honesty.py` | **28 passed, 1 skipped** |
| `tests/ui/test_s8_03_output_policy.py` | **included in above** |
| `tests/ui/test_s8_04_gui_state_acceptance.py` | **included in above** |
| **Total** | **124 passed, 1 skipped** |

---

## 6. Canonical Contracts Preserved

| Contract | Status |
|----------|--------|
| Canonical recovery eligibility (9 preconditions) | ✅ Preserved in `recovery.py` |
| Source integrity matrix | ✅ Enforced |
| Runtime artifact validation | ✅ Enforced |
| Failure classification | ✅ 3 classes preserved |
| Resume/Retry/Restart separation | ✅ Resume only; Retry/Restart NOT AUTHORIZED |
| `last_error` preservation | ✅ Preserved |
| Output/Runtime artifact separation | ✅ Maintained |
| Atomicity boundary | ✅ Project atomic, runtime non-atomic (DEFERRED) |
| Frozen runtime unchanged | ✅ NO modifications |
| Schema v1 frozen | ✅ NO changes |
| No Retry/Restart | ✅ NOT AUTHORIZED |
| No automatic source rebind | ✅ Not implemented |
| No Glossary | ✅ NOT IMPLEMENTED |

---

## 7. Validation

- Provider execution: **0**
- Network execution: **0**  
- Real translation: **0**
- Frozen runtime modified: **NO**
- Schema changed: **NO**
- Second persistence added: **NO**
- Automatic source rebind: **NO**
- Retry added: **NO**
- Restart added: **NO**
- Glossary UI: **NOT IMPLEMENTED**

---

## 8. Final Status

**Phase C Repair: PASS**

Ready for Phase D (Targeted Tests + Regression) and S9-07 (Reader-First E2E Acceptance).