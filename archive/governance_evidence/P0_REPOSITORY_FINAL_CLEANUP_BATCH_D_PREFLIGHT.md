# P0 Repository Final Cleanup — Batch D Preflight

## Generated Artifacts / Ignore Policy

**Baseline**: `9ed5ddbd178145e84811b608d74641debe7c82df`  
**Date**: 2026-08-23  
**Status**: PREFLIGHT COMPLETE

---

## 1. Modified Tracked Files (7 files) — Category D (Generated Artifacts)

| File | HEAD State | Worktree State | Classification | Decision |
|------|------------|----------------|----------------|----------|
| `artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json` | `status: "failed"` (provider timeout) | `status: "success"` (completed) | **IGNORE** — Canary progress tracker | Keep HEAD version; do not commit worktree change |
| `artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json` | `updated_at: "2026-08-07T00:42:12"` | `updated_at: "2026-08-08T00:48:09"` | **IGNORE** — Canary progress tracker | Keep HEAD version; do not commit worktree change |
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | `created_at: "2026-08-07T03:44:28"` | `created_at: "2026-08-14T18:57:17"` | **IGNORE** — Test output | Keep HEAD version; do not commit worktree change |
| `tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json` | `created_at: "2026-08-02T21:12:59"` | `created_at: "2026-08-14T23:20:12"` | **IGNORE** — Test output | Keep HEAD version; do not commit worktree change |
| `tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json` | `created_at: "2026-08-02T21:12:59"` | `created_at: "2026-08-14T23:20:12"` | **IGNORE** — Test output | Keep HEAD version; do not commit worktree change |
| `tests/literary/outputs/Regression_History.json` | 14 records (ends with PS-03-integration) | 17 records (adds TER-v1-integration, PS-03-smoke, PS-03) | **IGNORE** — Test history | Keep HEAD version; do not commit worktree change |
| `tests/literary/outputs/Regression_History.md` | 14 entries | 17 entries (adds TER-v1-integration, PS-03-smoke, PS-03) | **IGNORE** — Test history | Keep HEAD version; do not commit worktree change |

### Evidence for IGNORE Classification

- **No production consumer**: None of these 7 files are imported by production code (`core/`, `lts/`, `engine/`, `cli/`)
- **Test artifacts only**: All are outputs from canary runs or literary regression tests
- **Already in .gitignore**: `tests/literary/outputs/` is ignored (line 132)
- **Canary progress trackers**: The `*_live_progress.json` files are written by `tools/canary/run_canary.py` during canary execution
- **Literary test outputs**: Written by `ntpe_literary_evaluation.py` / `ntpe_literary_regression.py` during test runs
- **No clean-clone dependency**: Fresh clone does not need these files to run tests or production

---

## 2. Untracked Artifacts — Category C (Unrelated/Historical)

### `artifacts/p0_productization/` (16 files)
Governance/report files from P0 productization phase. Already have equivalents in `docs/governance/repository/` and `docs/governance/rm8/`.
**Classification**: **ARCHIVE** → Move to `archive/p0_productization/` or remove.

| File | Size | Note |
|------|------|------|
| `P0_ADAPTER_ARCHITECTURE.md` | 8.8KB | Has equivalent in governance docs |
| `P0_BASELINE_REGRESSION_DEBT_AUDIT.md` | 15.6KB | Historical audit |
| `P0_EPUB_INPUT_REQUIREMENTS.md` | 3.6KB | Requirements doc |
| `P0_GOVERNANCE_PROCESS_COMPLIANCE_AUDIT.md` | 11.3KB | Compliance audit |
| `P0_IMPLEMENTATION_SPECIFICATION.md` | 8.1KB | Spec |
| `P0_LEGACY_UI_CLASSIFICATION.md` | 5.2KB | Legacy classification |
| `P0_RM8_DELIVERY_REACHABILITY_REPORT.md` | 8.3KB | Delivery report |
| `P0_RM8_PROVENANCE_GAP_REPORT.md` | 6.9KB | Gap report |
| `P0_RM84_PACKAGING_CONTRACT_REPORT.md` | 6.7KB | Packaging contract |
| `P0_RUNTIME_CONTRACT_REPORT.md` | 7.6KB | Runtime contract |
| `P0_STAGE_EXECUTION_GOVERNANCE_CONTRACT.md` | 2.7KB | Governance contract |
| `P0_STAGE0_PREFLIGHT_COMPLETE.md` | 12.3KB | Preflight |
| `P0_STAGE1_INTEGRATED_ACCEPTANCE_REPORT.md` | 9.5KB | Acceptance report |
| `P0_STAGE2_IMPLEMENTATION_REPORT.md` | 5.6KB | Implementation report |
| `P0_STAGE3_IMPLEMENTATION_SPECIFICATION.md` | 45.5KB | Large spec |
| `P0_STAGE3_POSTFLIGHT_ROOT_ENTRIES.txt` | 1KB | Root entries |
| `P0_STAGE3_PREFLIGHT_ROOT_ENTRIES.txt` | 1KB | Root entries |
| `P0_UI_DIRECTORY_PROPOSAL.md` | 4.9KB | UI proposal |
| `P0_WORKING_TREE_CHANGE_INVENTORY.md` | 5.6KB | Inventory |

**Production Consumer**: **NONE** — Not imported by any production code.

### `artifacts/rm7_entity_canary/` (directory)
Entity canary run artifacts including:
- `consistency_report.json`, `entity_resolution.json`, `normalized_prompt.json`, `RM_7_3_1_CANARY_REPORT.md`
- `legacy/`, `runtime/`, `runtime_debug/`, `runtime_retry/`, `runtime_v4/` subdirectories with chunk outputs

**Classification**: **ARCHIVE** → Move to `archive/rm7_entity_canary/`

**Production Consumer**: **NONE** — Only referenced by `tools/canary/run_entity_canary.py` (canary tool, not production)

### `artifacts/rm8_5_audit/` (5 files)
RM8.5 audit reports:
- `RM_8_5_CONSISTENCY_AUDIT_REPORT.md` (29KB)
- `RM_8_5_LEGACY_CURRENT_CONTRACT_RECONCILIATION_INVENTORY.md` (31KB)
- `RM_8_5_Phase_1_Re-Implementation_Report.md` (5KB)
- `RM_8_5_PHASE2_REQUIREMENTS_ARCHITECTURE_INVENTORY.md` (15KB)
- `RM_8_5_REQUIREMENTS_ARCHITECTURE_INVENTORY.md` (37KB)

**Classification**: **ARCHIVE** → Move to `archive/rm8_5_audit/`

**Production Consumer**: **NONE** — Not imported by production code.

---

## 3. Untracked Data — Category C (Local-Only)

### `knowledge/learning/`
| File | Content | Classification |
|------|---------|----------------|
| `candidates.json` | Empty array `[]` | **IGNORE** — Local learning state |
| `characters.json` | 1 character entry (鄭泰義, LEARNING priority, confidence 0.7) | **IGNORE** — Local learning state |

**Evidence**:
- Referenced only in `core/knowledge_evolution/store.py` line 6 as comment: `knowledge/learning/ — LEARNING priority, AI candidate pool`
- Not imported by any production code
- `core/knowledge_evolution/` is not in production path (not in `core/` exports used by runtime)
- Clean clone does not need these files

**Decision**: **IGNORE** → Add `knowledge/` to `.gitignore`

---

## 4. Tracked Artifacts (Already in HEAD) — Category KEEP

The following tracked artifact directories contain governance evidence, freeze deltas, or historical release artifacts that are part of the repository's official record:

| Directory | Status | Rationale |
|-----------|--------|-----------|
| `artifacts/NTPE_TE_V6_0_0_FINAL_RELEASE_FREEZE_DELTA.zip` | KEEP | Release freeze delta |
| `artifacts/NTPE_TE_V6_0_STAGE10_*.zip` | KEEP | Stage deltas |
| `artifacts/NTPE_TE_V6_0_STAGE12_5_*.zip` | KEEP | Stage deltas |
| `artifacts/book_intake_stage28/` | KEEP | Freeze evidence |
| `artifacts/book_preparation_stage34/` | KEEP | Freeze evidence |
| `artifacts/controlled_*/` | KEEP | Controlled runtime evidence |
| `artifacts/knowledge_packages/v1/` | KEEP | Official knowledge packages |
| `artifacts/lcr_batch107/` | KEEP | LCR authorization evidence |
| `artifacts/lcr_batch107_review/` | KEEP | LCR review evidence |
| `artifacts/lcr_batch111/` | KEEP | Governance baseline evidence |
| `artifacts/ntpe_v20_stage*/` | KEEP | Stage 0/1 freeze evidence |
| `artifacts/te_v*/` | KEEP | TE validation evidence |
| `artifacts/tic_batch*/` | KEEP | TIC batch evidence |
| `artifacts/translation_execution_stage44/` | KEEP | Freeze evidence |

These are **repository source of truth** — they document the project's evolution, freeze decisions, and validation evidence.

---

## 5. .gitignore Current State vs Required Changes

### Already Ignored (Lines 132-141)
```
tests/literary/outputs/
output/
*_resume_state.json
*_manifest.json
*_chunk_*.json
*_zh.txt
```

### Required Additions
| Path | Reason |
|------|--------|
| `knowledge/` | Local learning state, not production data |
| `artifacts/p0_productization/` | Historical governance docs (archive instead) |
| `artifacts/rm7_entity_canary/` | Canary run artifacts |
| `artifacts/rm8_5_audit/` | Audit reports |

### Proposed .gitignore Additions
```gitignore
# --------------------------
# Local Learning Data
# --------------------------
knowledge/

# --------------------------
# Historical Artifacts (archived separately)
# --------------------------
artifacts/p0_productization/
artifacts/rm7_entity_canary/
artifacts/rm8_5_audit/
```

---

## 6. Clean-Clone Dependency Analysis

| Category | Required for Clean Clone? | Evidence |
|----------|---------------------------|----------|
| Modified tracked artifacts (7 files) | **NO** | Test outputs, canary progress |
| `artifacts/p0_productization/` | **NO** | Governance docs have equivalents in `docs/governance/` |
| `artifacts/rm7_entity_canary/` | **NO** | Canary evidence only |
| `artifacts/rm8_5_audit/` | **NO** | Audit reports only |
| `knowledge/` | **NO** | Local learning pool, empty on fresh clone |
| Tracked artifacts (zips, freeze evidence) | **YES** | Repository governance record |
| `knowledge_packages/v1/` | **YES** | Production knowledge packages |

---

## 7. Preflight Summary Matrix

| Item | Classification | Action |
|------|----------------|--------|
| 7 modified tracked files | **IGNORE** | Do not commit worktree changes; restore HEAD if needed |
| `artifacts/p0_productization/` (16 files) | **ARCHIVE** | Move to `archive/p0_productization/` |
| `artifacts/rm7_entity_canary/` (dir) | **ARCHIVE** | Move to `archive/rm7_entity_canary/` |
| `artifacts/rm8_5_audit/` (5 files) | **ARCHIVE** | Move to `archive/rm8_5_audit/` |
| `knowledge/learning/` (2 files) | **IGNORE** | Add `knowledge/` to `.gitignore` |
| Tracked artifact zips/evidence | **KEEP** | No action |
| `knowledge_packages/v1/` | **KEEP** | No action |

---

## 8. Stop Conditions Check

| Condition | Status |
|-----------|--------|
| Production consumer found | **CLEAR** — None |
| Clean clone needs untracked file | **CLEAR** — None required |
| UNKNOWN files | **CLEAR** — 0 |
| Frozen contract modification needed | **CLEAR** — None |
| Production code modification needed | **CLEAR** — None |
| Batch D/F scope confusion | **CLEAR** — Clear separation |

---

## 9. Validation Results (Current State)

| Gate | Result |
|------|--------|
| `python ntpe_validate.py` | ✅ PASS (1 pre-existing warning) |
| `git diff --check` | ✅ PASS (pre-existing CRLF only) |
| `python -m compileall core/` | ✅ PASS (2942 files) |
| Series regression | ✅ 281 PASS / 6 FAIL (pre-existing) |

---

## 10. Next Steps

**Preflight Complete. Awaiting Owner Authorization for Implementation.**

Implementation will:
1. Add `knowledge/`, `artifacts/p0_productization/`, `artifacts/rm7_entity_canary/`, `artifacts/rm8_5_audit/` to `.gitignore`
2. Move untracked artifact directories to `archive/`
3. Optionally restore HEAD versions of 7 modified tracked files (or leave as local modifications)
4. Validate all gates pass
5. Atomic commit

**No staging / commit / push performed in preflight phase.**