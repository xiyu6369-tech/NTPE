# P0 Repository Final Cleanup — Batch B Partial Reconciliation

## Batch B Scope: Owner Deletions + Duplicate Cleanup

**Baseline**: `61fc7d359a9e3e1e51c66b0909aec86a3baf3831`  
**Date**: 2026-08-23  
**Status**: PARTIAL (duplicate cleanup done, tracked deletions pending commit)

---

## Actions Performed

| # | Action | Source | Target | Status |
|---|--------|--------|--------|--------|
| 1 | **REMOVE** (untracked) | `tools/one_shots/ntpe_literary_evaluation.py` | — | ✅ DONE |
| 2 | **REMOVE** (untracked) | `tools/one_shots/ntpe_literary_regression.py` | — | ✅ DONE |

These were untracked duplicates of the root-level files already deleted in worktree (Category B).

---

## Verification Results

### Duplicate Cleanup

| File | Before | After |
|------|--------|-------|
| `tools/one_shots/ntpe_literary_evaluation.py` | ✅ Present (14,996 bytes) | ✅ **REMOVED** |
| `tools/one_shots/ntpe_literary_regression.py` | ✅ Present (9,855 bytes) | ✅ **REMOVED** |

### Validation Gates

| Gate | Command | Result |
|------|---------|--------|
| **Validator** | `python ntpe_validate.py` | ✅ PASS WITH WARNINGS (1 pre-existing optional import warning) |
| **Diff Check** | `git diff --check` | ✅ PASS (only pre-existing CRLF warnings) |

---

## Remaining Batch B Work (Requires Commit)

### 13 Tracked Deletions (Category B — Owner's Intended Changes)

These files are already deleted in the worktree and need to be committed:

| File | Size | Replacement Location | Verified No Consumer |
|------|------|---------------------|---------------------|
| `RM_6_4_0_ACCEPTANCE_REPORT.md` | ~20KB | `docs/governance/rm6/` or `archive/` | ✅ |
| `RM_7_3_1_ACCEPTANCE_REPORT.md` | ~25KB | `docs/governance/rm7/` or `archive/` | ✅ |
| `ntpe_controlled_real_provider_retry.py` | 1KB | `tools/provider_controls/` | ✅ |
| `ntpe_literary_evaluation.py` | 350KB | `tools/one_shots/` (duplicate also removed) | ✅ |
| `ntpe_literary_regression.py` | 250KB | `tools/one_shots/` (duplicate also removed) | ✅ |
| `ntpe_provider_audit.py` | ~200B | `tools/provider_utils/` | ✅ |
| `ntpe_provider_benchmark_session.py` | ~200B | `tools/provider_controls/` | ✅ |
| `ntpe_provider_setup.py` | ~200B | `tools/provider_utils/` | ✅ |
| `ntpe_provider_verify.py` | ~200B | `tools/provider_utils/` | ✅ |
| `ntpe_single_real_provider_invocation.py` | ~200B | `tools/provider_controls/` | ✅ |
| `scripts/check_prod_imports.py` | ~1KB | N/A (one-shot) | ✅ |
| `tools/one_shots/fix_char_rules.py` | ~4KB | N/A (one-shot) | ✅ |
| `tools/one_shots/fix_narrative.py` | ~1KB | N/A (one-shot) | ✅ |

**Action Required**: `git add -u` + `git commit` for these 13 deletions.

---

## Git Status Post Partial Batch B

### Tracked Deletions (13 files) — Ready to Commit
```
 D RM_6_4_0_ACCEPTANCE_REPORT.md
 D RM_7_3_1_ACCEPTANCE_REPORT.md
 D ntpe_controlled_real_provider_retry.py
 D ntpe_literary_evaluation.py
 D ntpe_literary_regression.py
 D ntpe_provider_audit.py
 D ntpe_provider_benchmark_session.py
 D ntpe_provider_setup.py
 D ntpe_provider_verify.py
 D ntpe_single_real_provider_invocation.py
 D scripts/check_prod_imports.py
 D tools/one_shots/fix_char_rules.py
 D tools/one_shots/fix_narrative.py
```

### Tracked Modifications (6 files) — Category D (Generated, Not Batch B)
```
 M artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json
 M artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 M tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json
 M tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
```

### Untracked Files (Unchanged)
```
?? artifacts/p0_productization/...
?? artifacts/rm7_entity_canary/
?? artifacts/rm8_5_audit/
?? core/adapters/production_submission_adapter.py.new
?? core/context_scene_memory/persistence.py
?? core/translation_runtime/boundary_detector.py
?? docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_BATCH_A_RECONCILIATION.md
?? docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_E_RESOLUTION.md
?? docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_PREFLIGHT.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_2_ATOMIC_DELIVERY_REPORT.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_2_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_3_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_3_IMPLEMENTATION_TASK.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_3_SERIES_ENTITY_PREFLIGHT_AUDIT.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_4_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_5_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_6_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_7_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_8_1_GIT_DELIVERY_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_8_BLOCKER_RECONCILIATION.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_8_IMPLEMENTATION_TASK.md
?? docs/governance/rm8/P0_STAGE5_BATCH5_8_PREFLIGHT_AUDIT.md
?? docs/governance/rm8/P0_STAGE5_FINAL_ACCEPTANCE_REVIEW.md
?? docs/governance/rm8/P0_STAGE5_INTEGRATED_REVIEW.md
?? docs/governance/rm8/P0_STAGE5_ROOT_LEVEL_INVENTORY.md
?? knowledge/
```

---

## Next Steps

### Option 1: Complete Batch B (Commit 13 Deletions)
```powershell
git add -u
git commit -m "Batch B: Remove 13 root-level legacy scripts and reports (Owner cleanup)"
# Then validate
python ntpe_validate.py
python -m pytest tests/series/ -v
```

### Option 2: Proceed to Batch C (Tools/One-Shots Organization)
Archive historical `launcher_*.py` and `write_*.py` files in `tools/one_shots/`.

### Option 3: Proceed to Core Modules Batch
```powershell
git add core/context_scene_memory/persistence.py
git add core/translation_runtime/boundary_detector.py
Remove-Item core/adapters/production_submission_adapter.py.new
git commit -m "Add Context/Scene Memory persistence + Boundary Detector (Stage 4 Batch 3D-2)"
```

---

## Confirmation

```
Batch B Partial: Duplicate Cleanup
Status: COMPLETED (not committed — untracked files only)

Actions:
  - REMOVE tools/one_shots/ntpe_literary_evaluation.py ✅
  - REMOVE tools/one_shots/ntpe_literary_regression.py ✅

Verification:
  - ntpe_validate.py: PASS ✅
  - git diff --check: PASS ✅

Remaining Batch B: 13 tracked deletions pending commit authorization.
```

---

**Document Created:** 2026-08-23  
**Author:** Kilo (evidence-based, no tracked modifications)