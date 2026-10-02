# NTPE S9-06 Phase C Repair Audit

**Date**: 2026-10-02
**Executor**: Kilo (Automated)
**Status**: `S9_06_PHASE_C_REPAIR_AUDIT_COMPLETE`

---

## 1. Current Wiring Audit

### 1.1 recovery.py
- ✅ Pure validation/decision responsibility only
- ✅ No translation/runtime logic
- ✅ Canonical `check_recovery_eligibility` with 9 preconditions
- ✅ Pure functions, no side effects

### 1.2 manager.py
- ✅ `validate_recovery_eligibility()` - application facade
- ✅ `get_recovery_blocked_reason()` - human-readable reason
- ✅ `validate_source_integrity()`, `validate_runtime_artifact()` - delegated to recovery.py
- ✅ Single application facade for recovery decisions

### 1.3 state.py
- ✅ `derive_state()` - canonical reader state derivation (reader_status, completed_units, etc.)
- ✅ No recovery eligibility logic (delegated to manager/view_model)
- ✅ `derive_reader_status()` - canonical reader status derivation

### 1.4 project_view_model.py
- ✅ `build_card_model()` - computes recovery eligibility via `check_recovery_eligibility()`
- ✅ Adds `recovery_eligible`, `recovery_blocked_reason`, `recovery_blocked_by` to `ProjectCardModel`
- ✅ Consumes manager result, doesn't re-derive

### 1.5 project_card.py
- ✅ Shows recovery badge: "可恢復" (green) when eligible, "不可恢復：原因" (red) when blocked
- ✅ Has `action_requested` signal for primary action
- ✅ Has `open_result_requested` and `reveal_folder_requested` for completed projects
- ❌ **No separate Recovery action signal** - only `action_requested` (used for both "開始翻譯" and "繼續翻譯")

### 1.6 project_page.py - _on_translate()
**CRITICAL ISSUE**: `_on_translate()` (normal translation start) is gated by `recovery_blocked_reason`:

```python
# S9-06: 恢復資格驗證 - 檢查專案是否有資格進行恢復/續翻
project_id = self._persisted_id_for_row(row)
if project_id and self._project_manager is not None:
    blocked_by, reason = self._project_manager.get_recovery_blocked_reason(project_id)
    if blocked_by:
        QMessageBox.warning(...)
        return
```

**This is WRONG**: Normal translation start (`_on_translate`) is blocked by recovery eligibility. A new project with no runtime artifact (eligible=false) cannot start normal translation.

### 1.6 project_page.py - Missing Recovery Action
- No separate Recovery action handler
- `action_requested` from card → `_on_card_action` → `_on_translate()` (same as "開始翻譯")
- No separate Recovery action that calls existing runtime resume

---

## 2. Audit Summary

| Check | Status | Notes |
|-------|--------|-------|
| recovery.py only decision/validation | ✅ PASS | Pure validation |
| Manager as sole app-level entry | ✅ PASS | Single facade |
| view_model only consumes | ✅ PASS | No re-derivation |
| _on_translate = Normal Translation | ❌ FAIL | Gated by recovery eligibility |
| Recovery action exists | ❌ FAIL | No separate recovery action |
| Recovery action calls existing resume | ❌ FAIL | No separate recovery action |
| Existing source_hash guard preserved | ✅ PASS | Runtime layer unchanged |
| Canonical eligibility source | ✅ PASS | recovery.py + manager facade |

---

## 3. Required Repairs

### 3.1 Fix _on_translate - Remove Recovery Gate
Normal translation (`_on_translate`) must NOT be gated by recovery eligibility. A new project with no runtime artifact MUST be able to start normal translation.

### 3.2 Add Separate Recovery Action
- Add `resume_requested` signal to `ProjectCard` (separate from `action_requested`)
- Add `_on_resume(project_id)` handler in `ProjectPage`
- Recovery action should call existing runtime resume mechanism (same as normal translation with `resume=True`)

### 3.3 Update ProjectCard
- Add `resume_requested` signal (emitted when "繼續翻譯" clicked)
- Only show "繼續翻譯" button when `recovery_eligible == True`

### 3.4 Wire Recovery Action to Existing Runtime Resume
- Recovery action should build options with `resume=True` (same as normal translation with resume)
- Use existing `_txt_output_dir` / `_build_epub_options` which already pass `resume=True`

### 3.4 Update ProjectCard UI
- Show "繼續翻譯" button only when `recovery_eligible == True`
- Show recovery blocked badge when blocked
- Emit `resume_requested` signal for recovery action

---

## 4. Repair Plan

1. **project_page.py**: Remove recovery gate from `_on_translate`; add `_on_resume` handler
2. **project_card.py**: Add `resume_requested` signal; show "繼續翻譯" button only when `recovery_eligible`
3. **project_page.py**: Add `_on_resume` handler that connects to `resume_requested` signal; call existing runtime with `resume=True`
4. **project_card.py**: Add "繼續翻譯" button conditionally; emit `resume_requested` signal
5. Tests: Verify normal translation works without recovery eligibility; recovery works when eligible

---

## 5. Audit Artifact

**Artifact**: `artifacts/NTPE_S9_06_PHASE_C_REPAIR_AUDIT.md` (this document)

**Status**: Audit complete. Ready for Phase C Repair implementation.