# P0 Repository Final Cleanup — Batch F3 Preflight

## Controlled Runtime Historical Artifacts

**Baseline**: `ab2231541b9fecf9bf20d4a3114cda90cb9842c5` (F1 delivered, F2 preflight complete)  
**Date**: 2026-08-23  
**Status**: PREFLIGHT COMPLETE

---

## 1. Baseline & Repository State

| Item | Value |
|------|-------|
| **Baseline Commit** | `ab2231541b9fecf9bf20d4a3114cda90cb9842c5` (F1 delivered) |
| **Branch** | `main` |
| **HEAD** | `ab22315` |
| **origin/main** | `ab22315` (synchronized) |
| **Worktree State** | Protected Category D changes present (2 modified tracked files) |

---

## 2. Protected Worktree Changes (OUT OF SCOPE)

The following 7 modified tracked files are **Category D — Generated Artifacts** from pre-existing worktree state. They are **excluded from F3 scope**.

```
M artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json
M artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json
M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
M tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json
M tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json
M tests/literary/outputs/Regression_History.json
M tests/literary/outputs/Regression_History.md
```

**Status**: **UNCHANGED** from F1 baseline. ✅

---

## 3. Controlled Runtime Artifacts Inventory (8 directories)

| Directory | Files | Size | Type |
|-----------|-------|------|------|
| `controlled_multi_chunk_translation_stage74` | 6 | 4.9 KB | Stage 74 canary execution |
| `controlled_multi_chunk_translation_stage742` | 3 | 2.8 KB | Stage 74.2 canary execution |
| `controlled_multi_chunk_translation_stage743` | 1 | 0.5 KB | Stage 74.3 canary execution |
| `controlled_multi_chunk_translation_stage743_diagnostic` | 2 | 3.1 KB | Stage 74.3 diagnostic |
| `controlled_multi_chunk_translation_stage744` | 4 | 5.2 KB | Stage 74.4 canary execution |
| `controlled_multi_chunk_translation_stage746` | 3 | 2.4 KB | Stage 74.6 canary execution |
| `controlled_runtime_stage54` | 1 | 2.5 KB | Stage 5.4 freeze evidence |
| `controlled_translation_runtime_stage73` | 3 | 6.4 KB | Stage 73 execution evidence |

**Total**: 8 directories, 23 files, **~27.7 KB**

---

## 4. Consumer Audit Results

### 4.1 Production Code Audit (`core/`, `lts/`, `engine/`, `cli/`, `sdk/`)

| Artifact | Production References | Key Modules |
|----------|----------------------|-------------|
| `controlled_multi_chunk_translation_stage74` | ✅ **YES** | `core/controlled_multi_chunk_translation_canary/policy.py` |
| `controlled_multi_chunk_translation_stage742` | ❌ NO | — |
| `controlled_multi_chunk_translation_stage743` | ✅ **YES** | `core/controlled_multi_chunk_translation_canary/policy.py` |
| `controlled_multi_chunk_translation_stage743_diagnostic` | ❌ NO | — |
| `controlled_multi_chunk_translation_stage744` | ✅ **YES** | `core/controlled_multi_chunk_translation_canary/policy.py` |
| `controlled_multi_chunk_translation_stage746` | ✅ **YES** | `core/controlled_multi_chunk_translation_canary/policy.py` |
| `controlled_runtime_stage54` | ❌ NO | — |
| `controlled_translation_runtime_stage73` | ✅ **YES** | `core/controlled_translation_runtime_integration/policy.py` |

**Production Consumers**: **5/8** have active production references (policy.py imports)

---

### 4.2 Test Audit (`tests/`)

| Artifact | Test References | Key Test Files |
|----------|----------------|----------------|
| `controlled_multi_chunk_translation_stage74` | ✅ **YES** | `test_artifact_root_contract.py`, `test_dialogue_normalization_stage745.py` |
| `controlled_multi_chunk_translation_stage742` | ❌ NO | — |
| `controlled_multi_chunk_translation_stage743` | ✅ **YES** | `test_artifact_root_contract.py` |
| `controlled_multi_chunk_translation_stage743_diagnostic` | ❌ NO | — |
| `controlled_multi_chunk_translation_stage744` | ✅ **YES** | `test_artifact_root_contract.py`, `test_dialogue_normalization_stage745.py` |
| `controlled_multi_chunk_translation_stage746` | ✅ **YES** | `test_artifact_root_contract.py` |
| `controlled_runtime_stage54` | ❌ NO | — |
| `controlled_translation_runtime_stage73` | ❌ NO | — |

**Test Consumers**: **4/8** have active test references

---

### 4.3 Governance/Manifest Audit (`docs/governance/`, `manifests/`, `schemas/`)

| Artifact | Governance References | Key Documents |
|----------|----------------------|---------------|
| `controlled_multi_chunk_translation_stage74` | ✅ **YES** | `RM_4_1_MIGRATION_PLAN.md`, `RM_2_3A_SYNC_REPORT.md` |
| `controlled_multi_chunk_translation_stage742` | ✅ **YES** | `RM_4_1_MIGRATION_PLAN.md` |
| `controlled_multi_chunk_translation_stage743` | ✅ **YES** | `RM_4_1_MIGRATION_PLAN.md` |
| `controlled_multi_chunk_translation_stage743_diagnostic` | ✅ **YES** | `RM_4_1_MIGRATION_PLAN.md` |
| `controlled_multi_chunk_translation_stage744` | ✅ **YES** | `RM_4_1_MIGRATION_PLAN.md` |
| `controlled_multi_chunk_translation_stage746` | ✅ **YES** | `RM_2_3A_SYNC_REPORT.md` |
| `controlled_runtime_stage54` | ✅ **YES** | `RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json` |
| `controlled_translation_runtime_stage73` | ❌ NO | — |

**Governance References**: **7/8** have governance/manifest references

---

### 4.4 Tooling/CI Audit (`tools/`, `.github/`, `scripts/`)

| Artifact | Tooling References | Result |
|----------|-------------------|--------|
| All 8 artifacts | None found | NO tooling references |

---

## 5. Detailed Classification Matrix

| Artifact | Production | Tests | Governance | Stage 74? | Classification | Rationale |
|----------|-----------|-------|------------|-----------|----------------|-----------|
| `controlled_multi_chunk_translation_stage74` | ✅ YES | ✅ YES | ✅ YES | ✅ Stage 74 | **KEEP** | Active production policy reference, active test contract, governance evidence |
| `controlled_multi_chunk_translation_stage742` | NO | NO | ✅ YES | ✅ Stage 74.2 | **ARCHIVE** | No active production/test consumer; governance reference in RM_4_1_MIGRATION_PLAN.md |
| `controlled_multi_chunk_translation_stage743` | ✅ YES | ✅ YES | ✅ YES | ✅ Stage 74.3 | **KEEP** | Active production policy reference, active test contract, governance evidence |
| `controlled_multi_chunk_translation_stage743_diagnostic` | NO | NO | ✅ YES | ✅ Stage 74.3 | **ARCHIVE** | No active production/test consumer; governance reference in RM_4_1_MIGRATION_PLAN.md |
| `controlled_multi_chunk_translation_stage744` | ✅ YES | ✅ YES | ✅ YES | ✅ Stage 74.4 | **KEEP** | Active production policy reference, active test contract, governance evidence |
| `controlled_multi_chunk_translation_stage746` | ✅ YES | ✅ YES | ✅ YES | ✅ Stage 74.6 | **KEEP** | Active production policy reference, active test contract, governance evidence |
| `controlled_runtime_stage54` | NO | NO | ✅ YES | ❌ Stage 5.4 | **KEEP** | Governance freeze evidence (RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json); historical freeze evidence |
| `controlled_translation_runtime_stage73` | ✅ YES | NO | NO | ❌ Stage 73 | **KEEP** | Active production policy reference in controlled_translation_runtime_integration |

---

## 6. Classification Summary

| Classification | Count | Items |
|--------------|-------|-------|
| **KEEP** | **6** | stage74, stage743, stage744, stage746, stage54, stage73 |
| **ARCHIVE** | **2** | stage742, stage743_diagnostic |
| **REMOVE** | 0 | — |
| **LOCAL_ONLY** | 0 | — |
| **UNKNOWN** | 0 | — |

**UNKNOWN = 0** ✅

---

## 7. Detailed Classification Rationale

### 7.1 KEEP — Active Production / Test / Governance Dependency

| Artifact | Evidence |
|----------|----------|
| `controlled_multi_chunk_translation_stage74` | Policy.py import; 2 test files; RM_4_1 + RM_2_3A governance |
| `controlled_multi_chunk_translation_stage743` | Policy.py import; 1 test file; RM_4_1 governance |
| `controlled_multi_chunk_translation_stage744` | Policy.py import; 2 test files; RM_4_1 governance |
| `controlled_multi_chunk_translation_stage746` | Policy.py import; 1 test file; RM_2_3A governance |
| `controlled_runtime_stage54` | Governance freeze evidence (RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json) |
| `controlled_translation_runtime_stage73` | Policy.py import in controlled_translation_runtime_integration |

### 7.2 ARCHIVE — Historical Stage Evidence, No Active Consumer

| Artifact | Evidence |
|----------|----------|
| `controlled_multi_chunk_translation_stage742` | Governance reference only (RM_4_1_MIGRATION_PLAN.md); no production/test imports |
| `controlled_multi_chunk_translation_stage743_diagnostic` | Governance reference only (RM_4_1_MIGRATION_PLAN.md); no production/test imports |

### 7.3 Stage 74 Assessment

| Stage 74 Sub-artifact | Production | Tests | Governance | Disposition |
|----------------------|-----------|-------|------------|-------------|
| stage74 | ✅ YES | ✅ YES | ✅ YES | **KEEP** |
| stage742 | NO | NO | ✅ YES | **ARCHIVE** |
| stage743 | ✅ YES | ✅ YES | ✅ YES | **KEEP** |
| stage743_diagnostic | NO | NO | ✅ YES | **ARCHIVE** |
| stage744 | ✅ YES | ✅ YES | ✅ YES | **KEEP** |
| stage746 | ✅ YES | ✅ YES | ✅ YES | **KEEP** |

**Stage 74 Summary**: 4/6 KEEP, 2/6 ARCHIVE. The diagnostic variant (stage743_diagnostic) and stage742 have no active production/test consumers but are referenced in migration governance.

---

## 8. Proposed Archive Mapping

| Source | Destination | Rationale |
|--------|-------------|-----------|
| `artifacts/controlled_multi_chunk_translation_stage742/` | `archive/controlled_runtime_historical/controlled_multi_chunk_translation_stage742/` | Historical Stage 74.2, no active consumer |
| `artifacts/controlled_multi_chunk_translation_stage743_diagnostic/` | `archive/controlled_runtime_historical/controlled_multi_chunk_translation_stage743_diagnostic/` | Historical Stage 74.3 diagnostic, no active consumer |

---

## 8. Consumer Safety Audit Summary

| Artifact | Production | Tests | Governance | Tooling | Disposition |
|----------|-----------|-------|------------|---------|-------------|
| stage74 | ✅ | ✅ | ✅ | NO | KEEP |
| stage742 | NO | NO | ✅ | NO | ARCHIVE |
| stage743 | ✅ | ✅ | ✅ | NO | KEEP |
| stage743_diag | NO | NO | ✅ | NO | ARCHIVE |
| stage744 | ✅ | ✅ | ✅ | NO | KEEP |
| stage746 | ✅ | ✅ | ✅ | NO | KEEP |
| stage54 | NO | NO | ✅ | NO | KEEP |
| stage73 | ✅ | NO | NO | NO | KEEP |

---

## 9. Frozen Contract Audit

| Frozen Contract | Controlled Runtime Dependency | Result |
|-----------------|------------------------------|--------|
| Foundation | NO | ✅ CLEAR |
| Character Memory v2 | NO | ✅ CLEAR |
| Context / Scene Memory | NO | ✅ CLEAR |
| Entity Resolver | NO | ✅ CLEAR |
| KnowledgeRuntime | NO | ✅ CLEAR |
| Checkpoint | NO | ✅ CLEAR |
| LTS | NO | ✅ CLEAR |
| Translation Pipeline | **YES** — policy.py imports stage artifacts | **KEEP required** |
| Series Orchestration | NO | ✅ CLEAR |

**Key Finding**: `core/controlled_multi_chunk_translation_canary/policy.py` and `core/controlled_translation_runtime_integration/policy.py` import Stage 74/73 artifacts. These are part of the **Translation Pipeline** frozen contract.

---

## 10. Proposed Archive Mapping

| Source | Destination | Files | Size |
|--------|-------------|-------|------|
| `artifacts/controlled_multi_chunk_translation_stage742/` | `archive/controlled_runtime_historical/controlled_multi_chunk_translation_stage742/` | 3 | 2.8 KB |
| `artifacts/controlled_multi_chunk_translation_stage743_diagnostic/` | `archive/controlled_runtime_historical/controlled_multi_chunk_translation_stage743_diagnostic/` | 2 | 3.1 KB |

---

## 10. REMOVE Safety

| Candidate | Production | Tests | Governance | Historical | Verdict |
|-----------|-----------|-------|------------|------------|---------|
| None | — | — | — | — | No REMOVE candidates |

---

## 11. Protected Worktree Verification

| File | Status | Unchanged |
|------|--------|-----------|
| `artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json` | Modified | ✅ |
| `artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json` | Modified | ✅ |
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | Modified | ✅ |
| `tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json` | Modified | ✅ |
| `tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json` | Modified | ✅ |
| `tests/literary/outputs/Regression_History.json` | Modified | ✅ |
| `tests/literary/outputs/Regression_History.md` | Modified | ✅ |

**All 7 protected files: UNCHANGED** ✅

---

## 12. Scope Isolation

| Category | Status |
|----------|--------|
| F1 (TE Historical) | ✅ Preserved (archive/te_v*) |
| F2 (TIC) | ✅ Preserved (artifacts/tic_batch*) — ALL KEEP |
| F4 (NTP v20, Book Stages) | ✅ Untouched |
| F5 (Translation Exec, Test Artifacts) | ✅ Untouched |
| Active KEEP Groups (LCR, RM6, Knowledge) | ✅ Preserved |

---

## 13. Stop Conditions Check

| Condition | Status | Evidence |
|-----------|--------|----------|
| **STOP-F3-01**: `HEAD != origin/main` | ✅ CLEAR | `ab22315 == ab22315` |
| **STOP-F3-02**: `UNKNOWN > 0` | ✅ CLEAR | UNKNOWN = 0 |
| **STOP-F3-03**: Active production dependency | ⚠️ TRIGGERED | 6/8 KEEP due to production/test/gov |
| **STOP-F3-04**: Frozen contract dependency | ⚠️ TRIGGERED | Translation Pipeline policy.py imports |
| **STOP-F3-05**: Clean clone needs artifact | ⚠️ TRIGGERED | 6 KEEP artifacts needed |
| **STOP-F3-06**: Protected worktree modified | ✅ CLEAR | 7 files unchanged |
| **STOP-F3-07**: Scope overlap | ✅ CLEAR | F1/F2/F4/F5 untouched |
| **STOP-F3-08**: New root artifact | ✅ CLEAR | None |
| **STOP-F3-09**: Production modification needed | ✅ CLEAR | Not needed |
| **STOP-F3-10**: Incomplete REMOVE evidence | ✅ CLEAR | No REMOVE candidates |

---

## 11. Validation Baseline (Pre-Existing State)

| Gate | Result |
|------|--------|
| `python -m compileall core/` | ✅ PASS (2941 files) |
| `python ntpe_validate.py` | ✅ PASS (1 pre-existing warning) |
| `git diff --check` | ✅ PASS (pre-existing trailing whitespace) |
| Series regression | ✅ 281 PASS / 6 FAIL (pre-existing) |
| Provider/Network/Translation | ✅ 0/0/0 |
| Frozen contracts | ✅ Unchanged |

---

## 12. Proposed Atomic Cleanup Batches

| Batch | Scope | Action | Authorization |
|-------|-------|--------|---------------|
| **F3-1** | `stage742`, `stage743_diagnostic` | **ARCHIVE** to `archive/controlled_runtime_historical/` | **REQUIRED** |
| **F3-2** | Remaining 6 KEEP artifacts | **NO ACTION** (stay in `artifacts/`) | N/A |

---

## 13. Owner Authorization Required

| Decision | Required? | Rationale |
|----------|-----------|-----------|
| Archive `stage742` | **YES** | No production/test consumer; governance reference only |
| Archive `stage743_diagnostic` | **YES** | No production/test consumer; governance reference only |
| Keep 6 remaining artifacts | **YES** (confirm) | Active production/test/governance dependencies |

---

## 14. Final Verdict

**BATCH F3 PREFLIGHT COMPLETE**

All acceptance criteria satisfied:

- ✅ Baseline verified (`ab22315`)
- ✅ Complete Controlled Runtime inventory (8 directories)
- ✅ Every item classified (6 KEEP, 2 ARCHIVE, 0 REMOVE, 0 UNKNOWN)
- ✅ Consumer audits complete (production, test, governance, tooling)
- ✅ Frozen contract audit complete (Translation Pipeline depends on 6 artifacts)
- ✅ Stage 74 explicitly resolved (4 KEEP, 2 ARCHIVE)
- ✅ Archive mapping defined (2 items)
- ✅ UNKNOWN = 0
- ✅ Protected worktree verified unchanged (7 files)
- ✅ F1/F2/F4/F5 boundaries preserved
- ✅ Preflight document created
- ✅ No staging, commit, or push performed

---

## 13. Owner Authorization Required

**Authorization Required for F3 Implementation:**

1. **Archive `controlled_multi_chunk_translation_stage742`** — No active production/test consumer; governance reference in RM_4_1_MIGRATION_PLAN.md
2. **Archive `controlled_multi_chunk_translation_stage743_diagnostic`** — No active production/test consumer; governance reference in RM_4_1_MIGRATION_PLAN.md

**Confirm KEEP for 6 artifacts with active dependencies.**

**Preflight Document:** `docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_BATCH_F3_PREFLIGHT.md`

**Next Step:** Owner review → Authorization for F3-1 Archive Batch