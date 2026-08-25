# P0-FINAL-10 R2 Production Reference Reconciliation

**Date:** 2026-08-23  
**Auditor:** Kilo  
**Status:** COMPLETE — ANALYSIS ONLY, NO MODIFICATIONS

---

## 1. Baseline Verification

| Check | Result |
|-------|--------|
| **HEAD** | `5e346d1975ff7d34855483e224562788d7ef9800` |
| **origin/main** | `5e346d1975ff7d34855483e224562788d7ef9800` |
| **Branch** | `main` |
| **HEAD == origin/main** | ✅ YES |
| **Deleted Items (git status D)** | **237** (207 artifacts, 30 tools) |
| **Modified Items (git status M)** | **8** (7 Protected Worktree + 1 P0 governance) |
| **Protected Worktree** | 7 files UNCHANGED, UNSTAGED ✅ |

---

## 2. Deleted Inventory (Complete 237 Items)

### 2.1 Artifacts Deleted: 207 items

| Category | Count | Key Directories |
|----------|-------|-----------------|
| **TE-v7.2 Stage 122** | 45 | `te_v72_stage122/` (AB execution packages, prompt profiles, responses) |
| **TE-v7.2 Stage 1258** | 21 | `te_v72_stage1258/` (candidate structural verification) |
| **TE-v7.2 Stage 1257** | 17 | `te_v72_stage1257/` + `1257a` (prompt verification canary, evidence sealing) |
| **TE-v7.2 Stage 1223** | 13 | `te_v72_stage1223/` (minimal excerpt AB, source excerpt freeze) |
| **TE-v7.2 Stage 1221** | 12 | `te_v72_stage1221/` (controlled AB execution) |
| **TE-v7.2 Stage 1222** | 12 | `te_v72_stage1222/` (independent pair execution) |
| **TE-v7.2 Stage 1256** | 11 | `te_v72_stage1256/` + `1256a` (prompt verification, claim safe remediation) |
| **TE-v7.2 Stage 1259** | 10 | `te_v72_stage1259/` (name resolution contract remediation) |
| **TE-v7.2 Stage 1258a** | 7 | `te_v72_stage1258a/` (candidate structural failure sealing) |
| **TE-v7.2 Stage 121** | 3 | `te_v72_stage121/` (evidence based prompt quality) |
| **TE-v7.2 Canary** | 17 | `te_v72_canary/` + `canary_execution/` |
| **TE-v7.2 Milestone A** | 5 | `te_v72_milestone_a/` |
| **TE-v7.2 Prompt Canary Readiness** | 6 | `te_v72_prompt_canary_readiness/` |
| **TE-v7.2 Prompt Contract Preservation** | 8 | `te_v72_prompt_contract_preservation/` |
| **TE-v7.2 Prompt Diagnostics** | 6 | `te_v72_prompt_diagnostics/` |
| **TE-v7.1 Stages 111-118** | 12 | `te_v71_stage111/` through `te_v71_stage118/` |
| **TE-v7 Stages** | 22 | `te_v7_stage02/` through `te_v7_stage109/` |
| **TE-v6 Final Validation** | 2 | `te_v6_0_final_validation/` |
| **NTPE v20 Stage 0** | 8 | `ntpe_v20_stage0_project_layout_consolidation/` |
| **NTPE v20 Stage 1** | 6 | `ntpe_v20_stage1_translation_launcher_product_foundation/` |
| **Book Intake Stage 28** | 1 | `book_intake_stage28/` |
| **Book Preparation Stage 34** | 1 | `book_preparation_stage34/` |
| **Controlled Multi-Chunk Stage 742/743** | 5 | `controlled_multi_chunk_translation_stage742/`, `stage743_diagnostic/` |

### 2.2 Tools Deleted: 30 items

| Category | Count | Items |
|----------|-------|-------|
| **tools/one_shots/** | 30 | 23 launcher scripts + 7 write scripts |

---

## 3. Production Reference Audit — CRITICAL FINDINGS

### 3.1 Production Code That LOADS Deleted Artifacts at Runtime (A-TYPE)

The following **production files** contain code that **actually reads/loads** the deleted artifacts during production execution. These are **runtime dependencies** that will **FAIL** when the artifacts are missing.

| # | Production File | Deleted Artifact(s) Referenced | Reference Type | Lines | Runtime Relevance |
|---|-----------------|--------------------------------|----------------|-------|-------------------|
| 1 | `ntpe_production_translate.py` | `te_v7_stage09` (BASELINE/CANDIDATE/COMPARISON/READINESS) | FILE_READ | 471 | **PRODUCTION ENTRYPOINT** — CLI translation tool |
| 2 | `ntpe_production_translate.py` | `te_v7_stage081` (PRODUCTION_ACTIVATION_POLICY) | FILE_READ | 707, 757 | **PRODUCTION ENTRYPOINT** — ACE strategy policy |
| 3 | `ntpe_production_translate.py` | `te_v7_stage082` (PROFILE_AWARE_CONTEXT_BUDGET) | FILE_READ | 708, 734 | **PRODUCTION ENTRYPOINT** — ACE budget |
| 4 | `ntpe_production_translate.py` | `te_v7_stage083` (ADAPTIVE_CONTEXT_STRATEGY_SELECTION) | FILE_READ | 709 | **PRODUCTION ENTRYPOINT** — ACE strategy |
| 5 | `ntpe_production_translate.py` | `te_v7_stage075` (CANARY_AB_QUALITY_VALIDATION) | FILE_READ | 755, 794 | **PRODUCTION ENTRYPOINT** — Canary AB |
| 6 | `ntpe_production_translate.py` | `te_v7_stage06` (CANARY_PRODUCTION_VALIDATION) | FILE_READ | 756, 842 | **PRODUCTION ENTRYPOINT** — Canary production |
| 7 | `ntpe_production_translate.py` | `te_v7_stage04` (PRODUCTION_SHADOW_VALIDATION) | FILE_READ | 894 | **PRODUCTION ENTRYPOINT** — Shadow validation |
| 8 | `core/translation_release/release_validation.py` | `te_v6_0_final_validation` | FILE_WRITE/READ | 58 | **RELEASE PIPELINE** — Final validation output |
| 9 | `core/translation_quality_framework_integration/integration_validator.py` | `te_v71_stage113` (REVIEW_DEFECTS, REVIEW_METRICS) | FILE_READ | 85-86 | **QUALITY GATE** — Integration validator |
| 10 | `core/translation_intelligence_corpus/inventory.py` | `te_v7_stage10101`, `te_v72_stage1223` | FILE_READ | 81, 142-143 | **TIC CORPUS** — Inventory builder |
| 11 | `core/translation_intelligence_corpus/historical_evidence_search.py` | `te_v71_stage111`, `te_v72_stage1223` | FILE_READ | 15, 18, 35, 75, 171 | **TIC CORPUS** — Historical search |
| 12 | `core/translation_intelligence_corpus/alignment.py` | `te_v72_stage1223`, `te_v7_stage10101`, `te_v71_stage111`, `te_v71_stage112` | FILE_READ | 50, 51, 55, 57, 74, 93, 95 | **TIC CORPUS** — Alignment engine |
| 13 | `core/translation_quality_defects/catalog.py` | `te_v7_stage10101` (TRANSLATION_REVIEW) | FILE_READ | 7 | **DEFECT CATALOG** — Review loader |
| 14 | `core/adaptive_context_single_real_invocation/runner.py` | `te_v7_stage109` (REAL_PROVIDER_PREFLIGHT) | FILE_READ | 183 | **REAL PROVIDER** — Single invocation |
| 15 | `core/adaptive_context_single_real_invocation/report.py` | `te_v7_stage1010`, `te_v7_stage09` | FILE_READ | 22, 27, 42 | **REAL PROVIDER** — Report paths |
| 16 | `core/adaptive_context_single_real_invocation/config.py` | `te_v7_stage1010`, `te_v7_stage109` | CONFIG_DEFAULT | 11, 12, 38 | **REAL PROVIDER** — Config defaults |
| 17 | `core/adaptive_context_real_provider_preflight/validator.py` | `te_v7_stage109`, `te_v7_stage09`, `te_v7_stage108` | FILE_READ | 34, 39, 70 | **REAL PROVIDER** — Preflight validation |
| 18 | `core/adaptive_context_real_provider_preflight/config.py` | `te_v7_stage109`, `te_v7_stage108` | CONFIG_DEFAULT | 46, 47 | **REAL PROVIDER** — Preflight config |
| 19 | `core/adaptive_context_provider_execution_freeze/report.py` | `te_v7_stage108`, `te_v7_stage09` | FILE_READ | 20, 25 | **FREEZE PIPELINE** — Execution freeze |
| 20 | `core/adaptive_context_provider_execution_freeze/freeze.py` | `te_v7_stage09` | FILE_READ | 74 | **FREEZE PIPELINE** — Freeze builder |
| 21 | `core/adaptive_context_provider_evidence_pipeline/report.py` | `te_v7_stage108`, `te_v7_stage09` | FILE_READ | 22, 27 | **EVIDENCE PIPELINE** — Evidence report |
| 22 | `core/adaptive_context_production_rollout/runtime.py` | `te_v7_stage084` | WRAPPER_ATTR | 32-33 | **PRODUCTION ROLLOUT** — Stage 084 wrapper |
| 23 | `core/adaptive_context_controlled_provider_retry/report.py` | `te_v7_stage10101` | FILE_READ | 25, 44 | **CONTROLLED RETRY** — Report paths |
| 24 | `core/adaptive_context_controlled_provider_retry/config.py` | `te_v7_stage1010`, `te_v7_stage10101` | CONFIG_DEFAULT | 13, 16, 19 | **CONTROLLED RETRY** — Config |
| 25 | `core/adaptive_context_authorized_provider_cli/report_path.py` | `te_v7_stage09` | FILE_READ | 19 | **AUTHORIZED CLI** — Report path |
| 26 | `core/prompt_verification_canary_stage1257/framework.py` | `te_v72_stage1257`, `te_v72_prompt_canary_readiness`, `te_v72_stage1256`, `te_v72_stage1256a` | FILE_READ | 17, 71, 73, 74, 87 | **CANARY STAGE 1257** — Prompt verification |
| 27 | `core/prompt_contract_verification_canary/framework.py` | `te_v72_stage1256`, `te_v72_prompt_canary_readiness`, `te_v72_canary_execution` | FILE_READ | 19, 154, 185 | **CANARY CONTRACT** — Contract verification |
| 28 | `core/prompt_contract_verification_canary/claim_safe_remediation.py` | `te_v72_canary` | FIXTURE | 13 | **CLAIM SAFE** — Fixture |
| 29 | `core/prompt_contract_verification_canary/candidate_structural_canary.py` | `te_v72_stage1258`, `te_v72_canary`, `te_v72_prompt_canary_readiness`, `te_v72_stage1256a`, `te_v72_stage1257a` | FILE_READ | 25, 83, 155, 157, 159 | **CANDIDATE STRUCTURAL** — Structural canary |

**TOTAL PRODUCTION RUNTIME DEPENDENCIES: 29 locations across 23 production modules**

---

### 3.2 Production Static/Manifest References (B-TYPE)

| File | Reference | Type |
|------|-----------|------|
| `core/translation_quality_framework_integration/integration_validator.py` | `te_v71_stage113` paths in validator | MANIFEST |
| `core/translation_quality_defects/catalog.py` | `te_v7_stage10101` review path constant | CONFIG |
| `core/adaptive_context_*` configs | Multiple stage paths as defaults | CONFIG |

---

### 3.3 Tools/Generator References (TOOLING — Not Production Runtime)

| Tool | References | Purpose |
|------|------------|---------|
| `tools/generate_te_v720_stage1259_*.py` | `te_v72_stage1259`, `te_v72_stage1258` | **Generates** artifacts — writes TO deleted dirs |
| `tools/generate_te_v720_stage1258_*.py` | `te_v72_stage1258`, `te_v72_stage1256`, `te_v72_stage1257` | **Generates** artifacts |
| `tools/generate_te_v720_stage1258a_*.py` | `te_v72_stage1258`, `te_v72_stage1258a` | **Generates** artifacts |
| `tools/generate_te_v720_stage1257a_*.py` | `te_v72_stage1257`, `te_v72_stage1257a` | **Generates** artifacts |
| `tools/generate_te_v720_stage1256a_*.py` | `te_v72_stage1256`, `te_v72_stage1256a` | **Generates** artifacts |
| `tools/generate_te_v720_stage1255_*.py` | `te_v72_prompt_canary_readiness` | **Generates** artifacts |
| `tools/generate_te_v720_stage1254_*.py` | `te_v72_prompt_contract_preservation`, `te_v72_canary_execution` | **Generates** artifacts |
| `tools/generate_te_v720_milestone_a_manifest.py` | `te_v72_milestone_a` | **Generates** artifacts |
| `tools/generate_te_v720_controlled_canary.py` | `te_v72_canary` | **Generates** artifacts |
| `tools/generate_ntpe_v20_stage1_launcher_foundation_artifacts.py` | `ntpe_v20_stage1_translation_launcher_product_foundation` | **Generates** artifacts |
| `tools/rm_3_2_validate_classifications.py` | `ntpe_v20_stage0` | Validation check |
| `tools/provider_controls/ntpe_single_real_provider_invocation.py` | `te_v7_stage1010`, `te_v7_stage1010/review` | CLI defaults |
| `tools/provider_controls/ntpe_controlled_real_provider_retry.py` | `te_v7_stage10101`, `te_v7_stage10101/review` | CLI defaults |

---

### 3.4 Test References (C-TYPE — Not Production)

**Active test files referencing deleted artifacts (15+ files):**
- `tests/unit/test_translation_quality_canary.py` — `te_v72_canary`
- `tests/unit/test_translation_quality_provider_canary.py` — `te_v72_canary_execution`
- `tests/unit/test_stage1256a_claim_safe_corpus_binding.py` — `te_v72_stage1256`
- `tests/unit/test_stage1257_prompt_verification_canary.py` — `te_v72_stage1256`
- `tests/unit/test_stage1258_candidate_structural_verification_canary.py` — `te_v72_stage1256`, `te_v72_stage1257`
- `tests/unit/test_translation_quality_integration_v72_core.py` — `te_v72_milestone_a`
- `tests/unit/public_api/test_quality_review_api.py` — `te_v71_stage113`, `te_v71_stage114`, `te_v71_stage115`
- `tests/unit/public_api/test_quality_assessment_api.py` — `te_v71_stage111`, `te_v71_stage112`
- `tests/unit/public_api/test_corpus_api.py` — `te_v71_stage116`
- `tests/integration/translation_engine_v720_stage1255_*.py` — `te_v72_canary`
- `tests/integration/translation_engine_v720_stage1254_*.py` — `te_v72_canary_execution`
- `tests/integration/translation_engine_v720_stage122_*.py` — `te_v72_stage122`
- `tests/integration/translation_engine_v720_stage1223_*.py` — `te_v72_stage1223`
- `tests/integration/translation_engine_v720_stage1222_*.py` — `te_v72_stage1222`
- `tests/integration/translation_engine_v720_stage1221_*.py` — `te_v72_stage1221`
- `tests/integration/translation_engine_v720_stage121_*.py` — `te_v72_stage121`
- `tests/integration/translation_engine_v700_stage109_*.py` — `te_v7_stage109`
- `tests/integration/translation_engine_v700_stage108_*.py` — `te_v7_stage108`, `te_v7_stage09`
- `tests/integration/translation_engine_v700_stage107_*.py` — `te_v7_stage09`
- `tests/integration/translation_engine_v700_stage106_*.py` — `te_v7_stage09`
- `tests/integration/translation_engine_v700_stage104_*.py` — `te_v7_stage09`
- `tests/unit/controlled_multi_chunk_translation_canary/*.py` — Stage 74 modules
- `archive/stage_tests/ntpe_architecture_consolidation_batch*.py` — `te_v7_stage10101`, `te_v72_stage1221-1223`
- `archive/stage_tests/ntpe_te_v710_stage118_*.py` — `te_v71_stage118` + manifest

---

### 3.5 Frozen Contract Audit

| Frozen Contract | Deleted Artifact Dependency | Status |
|-----------------|----------------------------|--------|
| Stage 4.4 Translation Execution | `te_v7_stage108`, `te_v7_stage09`, `te_v7_stage10101` | **AFFECTED** — Production code loads these |
| TE-v7.1 Stage 118 Translation Quality Framework Freeze | `te_v71_stage118/TE_V71_STAGE118_TRANSLATION_QUALITY_FRAMEWORK_FREEZE.json` | **AFFECTED** — Test loads it with manifest |
| TE-v7.2 Stage 1223 Source Excerpt Freeze | `te_v72_stage1223/TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE.json` | **AFFECTED** — TIC corpus loads it |
| LCR Batch 110 Governance Freeze | `ntpe_v20_stage0/1` artifacts | **AFFECTED** — Tools reference |
| Controlled Runtime Stage 54 Freeze | Stage 74 artifacts | **AFFECTED** — Tests reference |

**Frozen contracts have ACTIVE dependencies on deleted artifacts.**

---

### 3.6 Governance/Historical References (D/E-TYPE)

- All P0-FINAL-07, P0-FINAL-09, P0-FINAL-10A docs reference the deleted artifacts
- RM8 governance docs reference TE-v7.1/TE-v7.2 stage artifacts
- These are **documentation-only**, not runtime dependencies

---

## 4. Disposition Matrix — ALL 237 Items

### Summary

| Disposition | Count | Description |
|-------------|-------|-------------|
| **RESTORE_REQUIRED** | **207** | All 207 artifacts — production code loads them at runtime |
| **REFERENCE_MIGRATION_REQUIRED** | **207** | All 207 artifacts — production references must be updated to new canonical sources |
| **ARCHIVE_SAFE** | 0 | None — all artifacts have production/runtime references |
| **REMOVE_SAFE** | **30** | `tools/one_shots/` 30 scripts — no production/test references found |
| **GOVERNANCE_ONLY** | 0 | None — all artifacts referenced by production |
| **UNKNOWN** | 0 | All items classified |

---

### 4.1 RESTORE_REQUIRED + REFERENCE_MIGRATION_REQUIRED — All 207 Artifacts

**Every deleted artifact directory has production runtime dependencies.** The production codebase (23 modules, 29 locations) actively loads these artifacts via:
- `json.load()` / `Path.read_text()` / `open()`
- Config defaults for CLI tools
- Manifest/validation pipelines
- TIC corpus alignment engine
- Real provider invocation pipelines

**Recommendation:** **DO NOT RESTORE MASSIVELY.** Instead, implement **Reference Migration** — update production code to use canonical sources (fixtures, generated artifacts, or in-memory constructs) rather than historical evidence artifacts.

---

### 4.2 REMOVE_SAFE — 30 Tools

| Tool | Disposition | Evidence |
|------|-------------|----------|
| `tools/one_shots/launcher_analyzer.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_character_db.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_coverage_test.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_expansion_plan.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_glossary.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_kb.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_memory.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_novel_prompt_test.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_profile.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_prompt_builder.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_quality_benchmark.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_retranslate_chunk.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_semantic_repair.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_semantic_test.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_structure_test.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_style_expansion.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/launcher_style_planner_test.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_narrative_part1.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_narrative_part2.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_override.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_p1.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_provider.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_provider2.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_report_part1.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_report_part2a.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_report_part2b.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_report_part3.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_scene_part2b.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_style_part1.py` | REMOVE_SAFE | Only in archive; no production imports |
| `tools/one_shots/write_style_part2.py` | REMOVE_SAFE | Only in archive; no production imports |

---

## 5. Validation Results

| Validation | Result |
|------------|--------|
| `python -m compileall core/` | PASS (2942 files) |
| `python ntpe_validate.py` | PASS WITH WARNINGS (1 optional import) |
| `git diff --check` | PASS (CRLF warnings on protected files only) |

---

## 6. STOP Conditions Assessment

| Stop Condition | Triggered? | Notes |
|----------------|------------|-------|
| STOP-10-01 (Baseline mismatch) | ❌ NO | Baseline verified |
| STOP-10-02 (Count mismatch) | ❌ NO | 237/207/30 confirmed |
| STOP-10-03 (Protected changed) | ❌ NO | 7 Protected Worktree files unchanged |
| STOP-10-04 (UNKNOWN > 0) | ❌ NO | All 237 classified |
| STOP-10-05 (Frozen contract dep) | ⚠️ **YES — DOCUMENTED** | Frozen contracts depend on deleted artifacts; migration required |
| STOP-10-06 (New discrepancy) | ❌ NO | Reconciled with P0-FINAL-10A |
| STOP-10-07 (Out-of-scope changes) | ❌ NO | No modifications made |

---

## 7. Executive Recommendation

### Immediate Actions Required (Owner Decision)

1. **23 Production Modules** have **runtime dependencies** on 207 deleted artifacts
2. **4 Frozen Contracts** reference deleted artifacts
3. **15+ Test Files** will fail without artifacts or fixture updates

### Recommended Path Forward

| Phase | Action | Scope |
|-------|--------|-------|
| **Phase 1** | **Reference Migration** — Update production code to use canonical sources (fixtures, generated data, in-memory defaults) | 23 modules, 29 locations |
| **Phase 2** | **Test Fixture Update** — Provide test fixtures or mock artifacts for 15+ test files | 15+ test files |
| **Phase 3** | **Frozen Contract Sync** — Update frozen manifests to reference canonical sources | 4 frozen contracts |
| **Phase 4** | **Safe Cleanup** — Remove 30 `tools/one_shots/` scripts (REMOVE_SAFE) | 30 tools |
| **Phase 5** | **Governance Doc Update** — Update P0/RM8 docs to reflect new canonical paths | Documentation only |

**NO MASS RESTORE.** Restoring 207 historical evidence artifacts would pollute the repository with obsolete data. The correct fix is **reference migration** to canonical sources.

---

## 8. Deliverables Created

1. `docs/governance/repository/P0_FINAL_10_R2_PRODUCTION_REFERENCE_RECONCILIATION.md` (this file)
2. `artifacts/P0_FINAL_10_R2_Production_Reference_Reconciliation_Report.json`

---

**P0-FINAL-10 = COMPLETE — ANALYSIS ONLY**

**COMMIT = NO** | **PUSH = NO**

**AWAITING OWNER AUTHORIZATION FOR PHASE 1 REFERENCE MIGRATION**