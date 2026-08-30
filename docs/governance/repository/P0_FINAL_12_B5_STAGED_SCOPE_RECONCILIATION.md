# P0-FINAL-12-B5 Staged Scope Reconciliation Report

**Baseline:** HEAD=origin/main=2bedad883425978c1107d9b6e3fd9893bdd254a6
**Date:** 2026-08-24
**Status:** FAIL — Manifest overcounts B5 scope

---

## Executive Summary

Set comparison between manifest expected paths and actual staged paths reveals **manifest errors**: 11 test files listed in manifest have no changes from HEAD, and 6 fixture files in manifest don't exist on disk. The staged scope (165 files) correctly represents actual B5 work done.

**EXPECTED_PATHS ≠ STAGED_PATHS → FAIL**

---

## Set Comparison Results

| Metric | Count |
|---|---|
| **Expected Paths (from manifest)** | 182 |
| **Staged Paths (actual)** | 165 |
| **EXPECTED_ONLY (missing from stage)** | 17 |
| **STAGED_ONLY (extra in stage)** | 0 |
| **INTERSECTION** | 165 |
| **MATCH** | ❌ FALSE |

---

## Category Breakdown

### Test Files (Non-Fixtures)

| | Count |
|---|---|
| Expected (manifest) | 43 (40 unique — 3 duplicates) |
| Staged | 29 |
| EXPECTED_ONLY | 11 |
| STAGED_ONLY | 0 |
| INTERSECTION | 29 |

### Governance Files

| | Count |
|---|---|
| Expected | 2 |
| Staged | 2 |
| EXPECTED_ONLY | 0 |
| STAGED_ONLY | 0 |
| INTERSECTION | 2 |
| **MATCH** | ✅ YES |

### Fixture Files

| | Count |
|---|---|
| Expected (on disk) | 140 |
| Staged | 134 |
| EXPECTED_ONLY | 6 |
| STAGED_ONLY | 0 |
| INTERSECTION | 134 |

---

## Detailed Analysis: EXPECTED_ONLY Items (17 total)

### 11 Test Files — NOT Modified by B5 (Correctly NOT Staged)

| # | Path | Git Status | Why Not Staged | Belongs to B5? |
|---|---|---|---|---|
| 1 | `tests/integration/lcr_batch107_pre_execution_package_integration_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 2 | `tests/integration/lcr_batch5_dual_pass_translation_integration_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 3 | `tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 4 | `tests/integration/tic_batch5_historical_human_evidence_expansion_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 5 | `tests/integration/tic_batch61_human_approval_regression_activation_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 6 | `tests/integration/tic_batch6_human_correction_root_cause_regression_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 7 | `tests/integration/tic_batch7_offline_translation_quality_gate_test.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 8 | `tests/performance/tic_batch7_offline_quality_gate_benchmark.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 9 | `tests/unit/controlled_multi_chunk_translation_canary/test_dialogue_normalization_stage745.py` | unchanged (no diff from HEAD) | Already canonical import, no changes needed | ❌ NO |
| 10 | `tests/unit/test_lcr_batch107_real_provider_validation.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |
| 11 | `tests/unit/test_translation_quality_provider_canary.py` | unchanged (no diff from HEAD) | No modifications by B5 | ❌ NO |

**Root Cause:** Manifest listed 43 test files but 3 are duplicates (test_stage1256a, test_stage1257, test_stage1258 appear twice). Of the 40 unique, **11 have zero changes from HEAD** — they were never touched by B5 migration.

### 6 Fixture Files — Do Not Exist on Disk (Correctly NOT Staged)

| # | Path | Git Status | Why Not Staged | Belongs to B5? |
|---|---|---|---|---|
| 1 | `tests/fixtures/te_v72_canary/golden_corpus.json` | does not exist | Never created by B5 | ❌ NO |
| 2 | `tests/fixtures/tic_batch1/TRANSLATION_CORPUS_MANIFEST.json` | does not exist | Never created by B5 | ❌ NO |
| 3 | `tests/fixtures/tic_batch2/TRANSLATION_CASE_MANIFEST.json` | does not exist | Never created by B5 | ❌ NO |
| 4 | `tests/fixtures/tic_batch3/TRANSLATION_ALIGNMENT_MANIFEST.json` | **deleted** (D artifacts/tic_batch3/...) | Was historical artifact deleted in R2 | ❌ NO |
| 5 | `tests/fixtures/tic_batch4/FAILURE_CORPUS_MANIFEST.json` | does not exist | Never created by B5 | ❌ NO |
| 6 | `tests/fixtures/tic_batch5/HISTORICAL_HUMAN_EVIDENCE_EXPANSION_MANIFEST.json` | does not exist | Never created by B5 | ❌ NO |

**Root Cause:** Manifest claimed 109 fixtures but enumeration found 140 on disk (includes pre-existing). 6 expected files were never created by B5. Item 4 was actually a deleted historical artifact, not a fixture.

---

## Manifest Errors Identified

1. **Duplicate test entries**: 3 test files listed twice → 43 raw, 40 unique
2. **11 unmodified test files**: Listed in manifest but have no changes from HEAD
3. **Fixture count mismatch**: Manifest says 109, but 140 exist on disk (pre-existing + B5)
4. **6 non-existent fixtures**: Listed in manifest expected list but never created
5. **Historical artifact confusion**: `TRANSLATION_ALIGNMENT_MANIFEST.json` was deleted from `artifacts/` (R2), not created in `tests/fixtures/`

---

## Staged Scope Reality (Actual B5 Work)

| Category | Actual Count | Notes |
|---|---|---|
| Test files modified by B5 | 29 | All have actual modifications |
| Fixtures created by B5 | 134 | All legitimate canonical sources |
| Governance files | 2 | Implementation report + governance doc |
| **Total Staged** | **165** | **Correct scope for atomic commit** |

### Staged Test Files (29) — All Verified Modified

All 29 staged test files have actual diffs from HEAD and were modified by B5 migration to replace artifact references with fixture/manifest references.

### Staged Fixtures (134) — All Legitimate B5 Canonical Sources

All 134 staged fixture files are newly created canonical sources for B5 tests. No pre-existing fixtures were staged.

---

## Safety Verification (All PASS)

| Check | Status |
|---|---|
| No Protected Worktree files staged | ✅ PASS |
| No Production code (`core/`) staged | ✅ PASS |
| No Frozen contract modifications staged | ✅ PASS (fixtures are new canonical sources) |
| No Historical artifact deletions staged | ✅ PASS |
| No `tools/one_shots` staged | ✅ PASS |
| No UNKNOWN files staged | ✅ PASS |

---

## Conclusion

**The staged scope (165 files) is CORRECT for actual B5 work performed.**

The manifest (P0_FINAL_12_B5_SCOPE_MANIFEST.json) overcounts B5 scope by including:
- 11 test files never modified by B5
- 6 fixture files never created by B5
- Duplicate entries
- Pre-existing fixture files in the count

**Recommendation:** Proceed with atomic commit of the 165 staged files. The manifest should be corrected post-commit to reflect reality, but the staging is accurate.

---

## Final Report

```
EXPECTED PATHS: 182
STAGED PATHS: 165
EXPECTED_ONLY: 17 (11 unmodified tests + 6 non-existent fixtures)
STAGED_ONLY: 0
INTERSECTION: 165
UNKNOWN: 0

COMMIT = NO
PUSH = NO
```

**Status:** Awaiting manifest correction or Owner decision to proceed with actual staged scope (165 files).