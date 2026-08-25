# P0 Repository Final Cleanup — Batch F4 Preflight

## NTP v20 & Book Stages Historical Artifacts

**Baseline**: `1e3509d64493aeba5278d32a6b234c4dd86cdf27` (F3-1 delivered)  
**Date**: 2026-08-23  
**Status**: PREFLIGHT COMPLETE

---

## 1. Baseline & Repository State

| Item | Value |
|------|-------|
| **Baseline Commit** | `1e3509d64493aeba5278d32a6b234c4dd86cdf27` (F3-1 delivered) |
| **Branch** | `main` |
| **HEAD** | `1e3509d` |
| **origin/main** | `1e3509d` (synchronized) |
| **Worktree State** | Protected Category D changes present (2 modified tracked files) |

---

## 2. Protected Worktree Changes (OUT OF SCOPE)

The following 7 modified tracked files are **Category D — Generated Artifacts** from pre-existing worktree state. They are **excluded from F4 scope**.

```
M artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json
M artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json
M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
M tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json
M tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json
M tests/literary/outputs/Regression_History.json
M tests/literary/outputs/Regression_History.md
```

**Status**: **UNCHANGED** from F3-1 baseline. ✅

---

## 3. F4 Candidate Inventory (4 directories)

| Directory | Files | Size | Type |
|-----------|-------|------|------|
| `artifacts/book_intake_stage28/` | 1 | 1.8 KB | Book intake freeze evidence |
| `artifacts/book_preparation_stage34/` | 1 | 1.3 KB | Book preparation freeze evidence |
| `artifacts/ntpe_v20_stage0_project_layout_consolidation/` | 8 | 277.3 KB | Project layout consolidation evidence |
| `artifacts/ntpe_v20_stage1_translation_launcher_product_foundation/` | 6 | 6.6 KB | Stage 1 translation launcher foundation evidence |

**Total**: 4 directories, 16 files, **~287 KB**

---

## 4. Consumer Audit Results

### 4.1 Production Code Audit (`core/`, `lts/`, `engine/`, `cli/`, `sdk/`)

| Artifact | Production References | Result |
|----------|----------------------|--------|
| `book_intake_stage28` | ❌ NO | No production imports |
| `book_preparation_stage34` | ❌ NO | No production imports |
| `ntpe_v20_stage0_project_layout_consolidation` | ❌ NO | No production imports |
| `ntpe_v20_stage1_translation_launcher_product_foundation` | ❌ NO | No production imports |

**Production Consumers**: **0/4** have active production references.

---

### 4.2 Test Audit (`tests/`)

| Artifact | Test References | Result |
|----------|----------------|--------|
| `book_intake_stage28` | ❌ NO | No test references |
| `book_preparation_stage34` | ❌ NO | No test references |
| `ntpe_v20_stage0_project_layout_consolidation` | ❌ NO | No test references |
| `ntpe_v20_stage1_translation_launcher_product_foundation` | ❌ NO | No test references |

**Test Consumers**: **0/4** have active test references.

---

### 4.3 Governance/Manifest Audit (`docs/`, `manifests/`, `schemas/`)

| Artifact | Governance References | Key Documents |
|----------|----------------------|---------------|
| `book_intake_stage28` | ✅ YES | `RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json`, `BATCH_D_PREFLIGHT.md`, `BATCH_F_PREFLIGHT.md` |
| `book_preparation_stage34` | ✅ YES | `RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json`, `BATCH_D_PREFLIGHT.md` |
| `ntpe_v20_stage0_project_layout_consolidation` | ✅ YES | `PROJECT_LAYOUT.md`, `NTPE_GOVERNANCE_GAP_ANALYSIS.md`, `RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json`, `NTPE_REPOSITORY_STATUS_REPORT.md`, `NTPE_ROOT_DIRECTORY_GOVERNANCE_PLAN.md`, `ntpe_v20_stage0_project_layout_consolidation_manifest.json` |
| `ntpe_v20_stage1_translation_launcher_product_foundation` | ✅ YES | `RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json`, `NTPE_V20_STAGE1_TRANSLATION_LAUNCHER_PRODUCT_FOUNDATION.md`, `ntpe_v20_stage1_translation_launcher_product_foundation_manifest.json` |

**Governance References**: **4/4** have governance/manifest references.

---

### 4.4 Tooling/CI Audit (`tools/`, `.github/`, `scripts/`)

| Artifact | Tooling References | Result |
|----------|-------------------|--------|
| All 4 artifacts | None found | NO tooling references |

---

## 5. Classification Matrix

| Artifact | Production | Tests | Governance | Classification | Rationale |
|----------|-----------|-------|------------|----------------|-----------|
| `book_intake_stage28` | NO | NO | ✅ YES | **ARCHIVE** | Historical freeze evidence; no active production/test consumer; referenced in governance audit docs |
| `book_preparation_stage34` | NO | NO | ✅ YES | **ARCHIVE** | Historical freeze evidence; no active production/test consumer; referenced in governance audit docs |
| `ntpe_v20_stage0_project_layout_consolidation` | NO | NO | ✅ YES | **ARCHIVE** | Historical Stage 0/1 consolidation evidence; detailed manifests; no active production/test consumer |
| `ntpe_v20_stage1_translation_launcher_product_foundation` | NO | NO | ✅ YES | **ARCHIVE** | Historical Stage 1 launcher foundation evidence; release doc + manifest; no active production/test consumer |

---

## 6. Classification Summary

| Classification | Count | Items |
|--------------|-------|-------|
| **KEEP** | 0 | — |
| **ARCHIVE** | **4** | All 4 F4 candidates |
| **REMOVE** | 0 | — |
| **LOCAL_ONLY** | 0 | — |
| **UNKNOWN** | 0 | — |

**UNKNOWN = 0** ✅

---

## 7. Frozen Contract Audit

| Frozen Contract | F4 Artifact Dependency | Result |
|-----------------|----------------------|--------|
| Foundation | NO | ✅ CLEAR |
| Character Memory v2 | NO | ✅ CLEAR |
| Context / Scene Memory | NO | ✅ CLEAR |
| Entity Resolver | NO | ✅ CLEAR |
| KnowledgeRuntime | NO | ✅ CLEAR |
| Checkpoint | NO | ✅ CLEAR |
| LTS | NO | ✅ CLEAR |
| Translation Pipeline | NO | ✅ CLEAR |
| Series Orchestration | NO | ✅ CLEAR |

**Key Finding**: None of the F4 artifacts are required by any frozen contract. They are historical evidence artifacts only.

---

## 8. Proposed Archive Mapping

| Source | Destination | Files | Size |
|--------|-------------|-------|------|
| `artifacts/book_intake_stage28/` | `archive/book_stages_historical/book_intake_stage28/` | 1 | 1.8 KB |
| `artifacts/book_preparation_stage34/` | `archive/book_stages_historical/book_preparation_stage34/` | 1 | 1.3 KB |
| `artifacts/ntpe_v20_stage0_project_layout_consolidation/` | `archive/ntpe_v20_historical/ntpe_v20_stage0_project_layout_consolidation/` | 8 | 277.3 KB |
| `artifacts/ntpe_v20_stage1_translation_launcher_product_foundation/` | `archive/ntpe_v20_historical/ntpe_v20_stage1_translation_launcher_product_foundation/` | 6 | 6.6 KB |

---

## 9. Protected Worktree Verification

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

## 10. Scope Isolation

| Category | Status |
|----------|--------|
| F1 (TE Historical) | ✅ Preserved (archive/te_v*) |
| F2 (TIC) | ✅ Preserved (artifacts/tic_batch*) — ALL KEEP |
| F3 (Controlled Runtime) | ✅ Preserved (6 KEEP, 2 archived to controlled_runtime_historical/) |
| F5 (Translation Exec, Test Artifacts) | ✅ Untouched |
| Active KEEP Groups (LCR, RM6, Knowledge) | ✅ Preserved |

---

## 11. Stop Conditions Check

| Condition | Status | Evidence |
|-----------|--------|----------|
| **STOP-F4-01**: `HEAD != origin/main` | ✅ CLEAR | `1e3509d == 1e3509d` |
| **STOP-F4-02**: `UNKNOWN > 0` | ✅ CLEAR | UNKNOWN = 0 |
| **STOP-F4-03**: Active production consumer | ✅ CLEAR | 0/4 |
| **STOP-F4-04**: Frozen contract dependency | ✅ CLEAR | 0/4 |
| **STOP-F4-05**: Clean clone needs artifact | ✅ CLEAR | 0/4 |
| **STOP-F4-06**: Protected worktree modified | ✅ CLEAR | 7 files unchanged |
| **STOP-F4-07**: Scope overlap | ✅ CLEAR | F1/F2/F3/F5 untouched |
| **STOP-F4-08**: New root artifact | ✅ CLEAR | None |
| **STOP-F4-09**: Production modification needed | ✅ CLEAR | Not needed |

---

## 11. Validation Baseline (Pre-Existing State)

| Gate | Result |
|------|--------|
| `python -m compileall core/` | ✅ PASS (2941 files) |
| `python ntpe_validate.py` | ✅ PASS (1 pre-existing warning) |
| `git diff --check` | ✅ PASS (pre-existing CRLF only) |
| Series regression | ✅ 281 PASS / 6 FAIL (pre-existing) |
| Provider/Network/Translation | ✅ 0/0/0 |
| Frozen contracts | ✅ Unchanged |

---

## 12. Proposed Atomic Cleanup Batches

| Batch | Scope | Action | Authorization |
|-------|-------|--------|---------------|
| **F4-1** | Book Stages (2 dirs) | **ARCHIVE** to `archive/book_stages_historical/` | **REQUIRED** |
| **F4-2** | NTP v20 Stages (2 dirs) | **ARCHIVE** to `archive/ntpe_v20_historical/` | **REQUIRED** |

---

## 13. Owner Authorization Required

| Decision | Required? | Rationale |
|----------|-----------|-----------|
| Archive `book_intake_stage28` | **YES** | Historical freeze evidence, no active consumer |
| Archive `book_preparation_stage34` | **YES** | Historical freeze evidence, no active consumer |
| Archive `ntpe_v20_stage0_project_layout_consolidation` | **YES** | Historical Stage 0/1 consolidation evidence |
| Archive `ntpe_v20_stage1_translation_launcher_product_foundation` | **YES** | Historical Stage 1 launcher foundation evidence |

---

## 13. Final Verdict

**BATCH F4 PREFLIGHT COMPLETE**

All acceptance criteria satisfied:

- ✅ Baseline verified (`1e3509d`)
- ✅ Complete F4 inventory (4 directories, 16 files, 287 KB)
- ✅ Consumer audits complete (production, test, governance, tooling)
- ✅ Every candidate classified (0 KEEP, 4 ARCHIVE, 0 REMOVE, 0 UNKNOWN)
- ✅ UNKNOWN = 0
- ✅ Protected worktree verified unchanged (7 files)
- ✅ F1/F2/F3/F5 boundaries preserved
- ✅ Preflight document created
- ✅ No staging, commit, or push performed

---

## 14. Owner Authorization Required

**Authorization Required for F4 Implementation:**

1. **Archive `book_intake_stage28`** — Historical freeze evidence, no active consumer
2. **Archive `book_preparation_stage34`** — Historical freeze evidence, no active consumer
3. **Archive `ntpe_v20_stage0_project_layout_consolidation`** — Historical Stage 0/1 consolidation evidence
4. **Archive `ntpe_v20_stage1_translation_launcher_product_foundation`** — Historical Stage 1 launcher foundation evidence

**Preflight Document:** `docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_BATCH_F4_PREFLIGHT.md`

**Next Step:** Owner review → Authorization for F4-1/F4-2 Atomic Archive Batches